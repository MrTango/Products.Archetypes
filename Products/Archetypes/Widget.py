from types import DictType, FileType, ListType
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.Expression import Expression, createExprContext
from Products.Archetypes.utils import className, unique, capitalize
from Products.generator.widget import macrowidget
from Products.Archetypes.debug import log

from AccessControl import ClassSecurityInfo

from Acquisition import aq_base

try:
    True
except NameError:
    True=1
    False=0

class TypesWidget(macrowidget):
    __allow_access_to_unprotected_subobjects__ = 0
    _properties = macrowidget._properties.copy()
    _properties.update({
        'modes' : ('view', 'edit'),
        'populate' : 1,  # should this field be populated in edit and view?
        'postback' : 1,  # should this field be repopulated with POSTed
                         # value when an error occurs?
        'show_content_type' : 0,
        'helper_js': (),
        'helper_css': (),
        })

    security = ClassSecurityInfo()

    security.declarePublic('getName')
    def getName(self):
        return self.__class__.__name__

    security.declarePublic('getType')
    def getType(self):
        """Return the type of this field as a string"""
        return className(self)

    security.declarePublic('bootstrap')
    def bootstrap(self, instance):
        """Override if your widget needs data from the instance."""
        return

    security.declarePublic('populateProps')
    def populateProps(self, field):
        """This is called when the field is created."""
        name = field.getName()
        if not self.label:
            self.label = capitalize(name)

    security.declarePublic('isVisible')
    def isVisible(self, instance, mode='view'):
        """decide if a field is visible in a given mode -> 'state'
        visible, hidden, invisible"""
        # example: visible = { 'edit' :'hidden', 'view' : 'invisible' }
        vis_dic = getattr(aq_base(self), 'visible', None)
        state = 'visible'
        if not vis_dic:
            return state
        # ugly hack ...
        if type(vis_dic) == DictType:
            state = vis_dic.get(mode, state)
        return state

    # XXX
    security.declarePublic('setCondition')
    def setCondition(self, condition):
        """Set the widget expression condition."""
        self.condition = condition

    security.declarePublic('getCondition')
    def getCondition(self):
        """Return the widget text condition."""
        return self.condition

    security.declarePublic('testCondition')
    def testCondition(self, folder, portal, object):
        """Test the widget condition."""
        try:
            if self.condition:
                __traceback_info__ = (folder, portal, object, self.condition)
                ec = createExprContext(folder, portal, object)
                return Expression(self.condition)(ec)
            else:
                return 1
        except AttributeError:
            return 1

    # XXX
    security.declarePublic('process_form')
    def process_form(self, instance, field, form, empty_marker=None,
                     emptyReturnsMarker=False):
        """Basic impl for form processing in a widget"""
        value = form.get(field.getName(), empty_marker)
        if value is empty_marker:
            return empty_marker
        if emptyReturnsMarker and value == '':
            return empty_marker
        return value, {}

class VocabularyWidget(TypesWidget):

    security = ClassSecurityInfo()
    
    security.declarePublic('process_form')
    def process_form(self, instance, field, form, empty_marker=None,
                     emptyReturnsMarker=False):
        """Vocabulary impl for form processing in a widget"""
        value = form.get(field.getName(), empty_marker)
        value = field.Vocabulary(instance).getKeysFromIndexes(value)
            
        if value is empty_marker:
            return empty_marker
        if emptyReturnsMarker and value == '':
            return empty_marker
        
        return value, {}

class StringWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/string",
        'size' : '30',
        'maxlength' : '255',
        })

    security = ClassSecurityInfo()

class DecimalWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/decimal",
        'size' : '5',
        'maxlength' : '255',
        'dollars_and_cents' : 0,
        'whole_dollars' : 0,
        'thousands_commas' : 0,
        })

    security = ClassSecurityInfo()

class IntegerWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/integer",
        'size' : '5',
        'maxlength' : '255',
        })

    security = ClassSecurityInfo()

class ReferenceWidget(VocabularyWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/reference",
        'checkbox_bound': 5,

        'addable' : 0, # create createObject link for every addable type
        'destination' : None, # may be:
                              # - ".", context object;
                              # - None, any place where 
                              #   Field.allowed_types can be added;
                              # - string path;
                              # - name of method on instance
                              #   (it can be a combination list);
                              # - a list, combining all item above;
                              # - a dict, where
                              #   {portal_type:<combination of the items above>}
                              # destination is relative to portal root
        'helper_css' : ('content_types.css',),
        })

    security = ClassSecurityInfo()

    security.declarePublic('addableTypes')
    def addableTypes(self, instance, field):
        """Returns a list of dictionaries which maps portal_type to its human readable
        form."""
        def lookupDestinationsFor(typeinfo, tool, purl):
            """
            search where the user can add a typeid instance
            """
            # first, discover who can contain the type
            searchFor = []
            for regType in tool.listTypeInfo():
                if typeinfo.globalAllow():
                    searchFor.append(regType.getId())
                elif regType.filter_content_types and \
                    typeinfo.getId() in regType.allowed_content_types:
                    searchFor.append(regType.getId())
            # after, gimme the path/s
            containers = []
            for wanted in searchFor:
                for brain in \
                    instance.portal_catalog(portal_type=wanted):
                    obj = brain.getObject()
                    if obj != None and \
                        hasattr(obj.aq_explicit,'isPrincipiaFolderish'):
                        containers.append(purl.getRelativeUrl(obj))
            # ok, go on...
            return containers

        tool = getToolByName(instance, 'portal_types')
        purl = getToolByName(instance, 'portal_url')
        types = []

        options = {}
        for typeid in field.allowed_types:
            if self.destination == None:
                options[typeid]=[None]
            elif isinstance(self.destination, DictType):
                options[typeid]=self.destination.get(typeid, [None])
            elif isinstance(self.destination, ListType):
                options[typeid]=self.destination
            else:
                place = getattr(aq_base(instance), self.destination,
                    self.destination)
                if callable(place):
                    place = place()
                if isinstance(place, ListType):
                    options[typeid] = place
                else:
                    options[typeid] = [place]

        for typeid in field.allowed_types:
            info = tool.getTypeInfo(typeid)
            if info is None:
                log("Warning: in Archetypes.Widget.lookupDestinationsFor: portal type %s not found" % typeid )
                continue

            value = {}
            value['id'] = typeid
            value['name'] = info.Title()
            value['destinations'] = []
                
            for option in options.get(typeid):
                if option == None:
                    value['destinations'] = value['destinations'] + \
                        lookupDestinationsFor(info, tool, purl)
                elif option == '.':
                    value['destinations'].append(
                        purl.getRelativeContentURL(instance) )
                else:
                    place = getattr(aq_base(instance), self.destination,
                        self.destination)
                    if callable(place):
                        place = place()
                    if isinstance(place, ListType):
                        value['destinations'] = place + \
                             value['destinations']
                    else:
                        value['destinations'].append(place)

            if value['destinations']:
                types.append(value)

        return types

class ComputedWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/computed",
        })

    security = ClassSecurityInfo()

class TextAreaWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/textarea",
        'rows'  : 5,
        'cols'  : 40,
        'format': 0,
        'append_only':0,
        'divider':"\n\n========================\n\n",
        })

    security = ClassSecurityInfo()

    # XXX
    security.declarePublic('process_form')
    def process_form(self, instance, field, form, empty_marker=None,
                     emptyReturnsMarker=False):
        """handle text formatting"""
        text_format = None
        value = None
        # text field with formatting
        value = form.get(field.getName(), empty_marker)

        if value is empty_marker:
            return empty_marker

        if emptyReturnsMarker and value == '':
            return empty_marker

        if hasattr(field, 'allowable_content_types') and \
               field.allowable_content_types:
            format_field = "%s_text_format" % field.getName()
            text_format = form.get(format_field, empty_marker)
        kwargs = {}

        if text_format is not empty_marker and text_format:
            kwargs['mimetype'] = text_format

        """ handle append_only  """
        # SPANKY: It would be nice to add a datestamp too, if desired

        # Don't append if the existing data is empty or nothing was passed in
        if getattr(field.widget, 'append_only', None) and (value and not value.isspace()):
            if field.get(instance):
                # using default_output_type caused a recursive transformation
                # that sucked, thus mimetype= here to keep it in line
                value = value + field.widget.divider + field.get(instance, mimetype="text/plain")
            
        return value, kwargs

class LinesWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/lines",
        'rows'  : 5,
        'cols'  : 40,
        })

    security = ClassSecurityInfo()

class BooleanWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/boolean",
        })

    security = ClassSecurityInfo()

class CalendarWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/calendar",
        'format' : '', # time.strftime string
        'helper_js': ('jscalendar/calendar_stripped.js',
                      'jscalendar/calendar-en.js'),
        'helper_css': ('jscalendar/calendar-system.css',),
        })

    security = ClassSecurityInfo()

class SelectionWidget(VocabularyWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'format': "flex", # possible values: flex, select, radio
        'macro' : "widgets/selection",
        })

    security = ClassSecurityInfo()

class MultiSelectionWidget(VocabularyWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'format': "select", # possible values: select, checkbox
        'macro' : "widgets/multiselection",
        'size'  : 5,
        })

    security = ClassSecurityInfo()

class KeywordWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/keyword",
        'size'  : 5,
        'vocab_source' : 'portal_catalog',
        'roleBasedAdd' : 1,
        })

    security = ClassSecurityInfo()

    # XXX
    security.declarePublic('process_form')
    def process_form(self, instance, field, form, empty_marker=None,
                     emptyReturnsMarker=False):
        """process keywords from form where this widget has a list of
        available keywords and any new ones"""
        name = field.getName()
        existing_keywords = form.get('%s_existing_keywords' % name, empty_marker)
        if existing_keywords is empty_marker:
            existing_keywords = []
        new_keywords = form.get('%s_keywords' % name, empty_marker)
        if new_keywords is empty_marker:
            new_keywords = []

        value = existing_keywords + new_keywords
        value = [k for k in list(unique(value)) if k]

        if not value and emptyReturnsMarker: return empty_marker

        return value, {}


class FileWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/file",
        'show_content_type' : 1,
        })

    security = ClassSecurityInfo()

    # XXX
    security.declarePublic('process_form')
    def process_form(self, instance, field, form, empty_marker=None,
                     emptyReturnsMarker=False):
        """form processing that deals with binary data"""

        delete = form.get('%s_delete' % field.getName(), empty_marker)
        if delete is not empty_marker: return "DELETE_FILE", {}

        value = None

        fileobj = form.get('%s_file' % field.getName(), empty_marker)

        if fileobj is empty_marker: return empty_marker

        filename = getattr(fileobj, 'filename', '') or \
                   (isinstance(fileobj, FileType) and \
                    getattr(fileobj, 'name', ''))

        if filename:
            value = fileobj

        if not value: return None

        return value, {}


class RichWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/rich",
        'rows'  : 5,
        'cols'  : 40,
        'format': 1,
        'allow_file_upload':1, 
        })

    security = ClassSecurityInfo()

    # XXX
    security.declarePublic('process_form')
    def process_form(self, instance, field, form, empty_marker=None,
                     emptyReturnsMarker=False):
        """complex form processing, includes handling for text
        formatting and file objects"""
        # This is basically the old processing chain from base object
        text_format = None
        isFile = 0
        value = None

        # text field with formatting
        if hasattr(field, 'allowable_content_types') and \
           field.allowable_content_types:
            # was a mimetype specified
            format_field = "%s_text_format" % field.getName()
            text_format = form.get(format_field, empty_marker)

        # or a file?
        fileobj = form.get('%s_file' % field.getName(), empty_marker)

        if fileobj is not empty_marker:

            filename = getattr(fileobj, 'filename', '') or \
                       (isinstance(fileobj, FileType) and \
                        getattr(fileobj, 'name', ''))

            if filename:
                value = fileobj
                isFile = 1

        kwargs = {}
        if not value:
            value = form.get(field.getName(), empty_marker)
            if text_format is not empty_marker and text_format:
                kwargs['mimetype'] = text_format

        if value is empty_marker: return empty_marker

        if value and not isFile:
            # Value filled, no file uploaded
            if kwargs.get('mimetype') == str(field.getContentType(instance)) \
                   and instance.isBinary(field.getName()):
                # Was an uploaded file, same content type
                del kwargs['mimetype']

        return value, kwargs


class IdWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/zid",
         # show IDs in edit boxes when they are autogenerated?
        'display_autogenerated' : 1,
        # script used to determine if an ID is autogenerated
        'is_autogenerated' : 'isIDAutoGenerated',
        })

    security = ClassSecurityInfo()

    # XXX
    security.declarePublic('process_form')
    def process_form(self, instance, field, form, empty_marker=None,
                     emptyReturnsMarker=False):
        """the id might be hidden by the widget and not submitted"""
        value = form.get('id', empty_marker)
        if not value or value is empty_marker or not value.strip():
            value = instance.getId()
        return value,  {}

class ImageWidget(FileWidget):
    __allow_access_to_unprotected_subobjects__ = 0
    _properties = FileWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/image",
        # only display if size <= threshold, otherwise show link
        'display_threshold': 102400,
        })

    security = ClassSecurityInfo()

    # XXX
    security.declarePublic('process_form')
    def process_form(self, instance, field, form, empty_marker=None,
                     emptyReturnsMarker=False):
        """form processing that deals with image data (and its delete case)"""
        value = None
        ## check to see if the delete hidden was selected
        delete = form.get('%s_delete' % field.getName(), empty_marker)
        if delete is not empty_marker: return "DELETE_IMAGE", {}

        fileobj = form.get('%s_file' % field.getName(), empty_marker)

        if fileobj is empty_marker: return empty_marker

        filename = getattr(fileobj, 'filename', '') or \
                   (isinstance(fileobj, FileType) and \
                    getattr(fileobj, 'name', ''))

        if filename:
            value = fileobj

        if not value: return None
        return value, {}


# LabelWidgets are used to display instructions on a form.  The widget only
# displays the label for a value -- no values and no form elements.
class LabelWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/label",
        })

    security = ClassSecurityInfo()

class PasswordWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : 'widgets/password',
        'modes' : ('edit',),
        'populate' : 0,
        'postback' : 0,
        'size' : 20,
        'maxlength' : '255',
        })

    security = ClassSecurityInfo()

class VisualWidget(TextAreaWidget):
    __allow_access_to_unprotected_subobjects__ = 0
    _properties = TextAreaWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/visual",
        'rows'  : 25,      #rows of TextArea if VE is not available
        'cols'  : 80,      #same for cols
        'width' : '507px', #width of VE frame (if VE is avalilable)
        'height': '400px', #same for height
        'format': 0,
        'append_only':0, #creates a textarea you can only add to, not edit
        'divider': '\n\n<hr />\n\n', # default divider for append only divider
        })

    security = ClassSecurityInfo()

class EpozWidget(TextAreaWidget):
    __allow_access_to_unprotected_subobjects__ = 0
    _properties = TextAreaWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/epoz",
        })

    security = ClassSecurityInfo()

class InAndOutWidget(VocabularyWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/inandout",
        'size' : '6',
        'helper_js': ('widgets/js/inandout.js',),
        })

    security = ClassSecurityInfo()

class PicklistWidget(VocabularyWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/picklist",
        'size' : '6',
        'helper_js': ('widgets/js/picklist.js',),
        })

    security = ClassSecurityInfo()

__all__ = ('StringWidget', 'DecimalWidget', 'IntegerWidget',
           'ReferenceWidget', 'ComputedWidget', 'TextAreaWidget',
           'LinesWidget', 'BooleanWidget', 'CalendarWidget',
           'SelectionWidget', 'MultiSelectionWidget', 'KeywordWidget',
           'RichWidget', 'FileWidget', 'IdWidget', 'ImageWidget',
           'LabelWidget', 'PasswordWidget', 'VisualWidget', 'EpozWidget',
           'InAndOutWidget', 'PicklistWidget',)

from Registry import registerWidget

registerWidget(StringWidget,
               title='String',
               description=('Renders a HTML text input box which '
                            'accepts a single line of text'),
               used_for=('Products.Archetypes.Field.StringField',)
               )

registerWidget(DecimalWidget,
               title='Decimal',
               description=('Renders a HTML text input box which '
                            'accepts a fixed point value'),
               used_for=('Products.Archetypes.Field.FixedPointField',)
               )

registerWidget(IntegerWidget,
               title='Integer',
               description=('Renders a HTML text input box which '
                            'accepts a integer value'),
               used_for=('Products.Archetypes.Field.IntegerField',)
               )

registerWidget(ReferenceWidget,
               title='Reference',
               description=('Renders a HTML text input box which '
                            'accepts a reference value'),
               used_for=('Products.Archetypes.Field.IntegerField',)
               )

registerWidget(ComputedWidget,
               title='Computed',
               description='Renders the computed value as HTML',
               used_for=('Products.Archetypes.Field.ComputedField',)
               )

registerWidget(TextAreaWidget,
               title='Text Area',
               description=('Renders a HTML Text Area for typing '
                            'a few lines of text'),
               used_for=('Products.Archetypes.Field.StringField',
                         'Products.Archetypes.Field.TextField')
               )

registerWidget(LinesWidget,
               title='Lines',
               description=('Renders a HTML textarea for a list '
                            'of values, one per line'),
               used_for=('Products.Archetypes.Field.LinesField',)
               )

registerWidget(BooleanWidget,
               title='Boolean',
               description='Renders a HTML checkbox',
               used_for=('Products.Archetypes.Field.BooleanField',)
               )

registerWidget(CalendarWidget,
               title='Calendar',
               description=('Renders a HTML input box with a helper '
                            'popup box for choosing dates'),
               used_for=('Products.Archetypes.Field.DateTimeField',)
               )

registerWidget(SelectionWidget,
               title='Selection',
               description=('Renders a HTML selection widget, which '
                            'can be represented as a dropdown, or as '
                            'a group of radio buttons'),
               used_for=('Products.Archetypes.Field.StringField',
                         'Products.Archetypes.Field.LinesField',)
               )

registerWidget(MultiSelectionWidget,
               title='Multi Selection',
               description=('Renders a HTML selection widget, where '
                            'you can be choose more than one value'),
               used_for=('Products.Archetypes.Field.LinesField',)
               )

registerWidget(KeywordWidget,
               title='Keyword',
               description='Renders a HTML widget for choosing keywords',
               used_for=('Products.Archetypes.Field.LinesField',)
               )

registerWidget(RichWidget,
               title='Rich Widget',
               description=('Renders a HTML widget that allows you to '
                            'type some content, choose formatting '
                            'and/or upload a file'),
               used_for=('Products.Archetypes.Field.TextField',)
               )

registerWidget(FileWidget,
               title='File',
               description='Renders a HTML widget upload a file',
               used_for=('Products.Archetypes.Field.FileField',)
               )

registerWidget(IdWidget,
               title='ID',
               description='Renders a HTML widget for typing an Id',
               used_for=('Products.Archetypes.Field.StringField',)
               )

registerWidget(ImageWidget,
               title='Image',
               description=('Renders a HTML widget for '
                            'uploading/displaying an image'),
               used_for=('Products.Archetypes.Field.ImageField',)
               )

registerWidget(LabelWidget,
               title='Label',
               description=('Renders a HTML widget that only '
                            'displays the label'),
               used_for=None
               )

registerWidget(PasswordWidget,
               title='Password',
               description='Renders a HTML password widget',
               used_for=('Products.Archetypes.Field.StringField',)
               )

registerWidget(VisualWidget,
               title='Visual',
               description='Renders a HTML visual editing widget widget',
               used_for=('Products.Archetypes.Field.StringField',)
               )

registerWidget(EpozWidget,
               title='Epoz',
               description='Renders a HTML Epoz widget',
               used_for=('Products.Archetypes.Field.StringField',)
               )

registerWidget(InAndOutWidget,
               title='In & Out',
               description=('Renders a widget for moving items '
                            'from one list to another. Items are '
                            'removed from the first list.'),
               used_for=('Products.Archetypes.Field.LinesField',)
               )

registerWidget(PicklistWidget,
               title='Picklist',
               description=('Render a widget to pick from one '
                            'list to populate another.  Items '
                            'stay in the first list.'),
               used_for=('Products.Archetypes.Field.LinesField',)
               )

from Registry import registerPropertyType

registerPropertyType('maxlength', 'integer', StringWidget)
registerPropertyType('populate', 'boolean')
registerPropertyType('postback', 'boolean')
registerPropertyType('rows', 'integer', RichWidget)
registerPropertyType('cols', 'integer', RichWidget)
registerPropertyType('rows', 'integer', TextAreaWidget)
registerPropertyType('cols', 'integer', TextAreaWidget)
registerPropertyType('append_only', 'boolean', TextAreaWidget)
registerPropertyType('divider', 'string', TextAreaWidget)
registerPropertyType('rows', 'integer', LinesWidget)
registerPropertyType('cols', 'integer', LinesWidget)
registerPropertyType('rows', 'integer', VisualWidget)
registerPropertyType('cols', 'integer', VisualWidget)
