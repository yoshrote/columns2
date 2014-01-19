import colander
from lxml import etree
import cgi
from BeautifulSoup import BeautifulSoup

class StrippingString(colander.String):
    def deserialize(self, node, cstruct):
        result = super(StrippingString, self).deserialize(node, cstruct)
        if result:
            return result.strip()
        else:
            return result
    

class FieldStorage(object):
    """
    Handles cgi.FieldStorage instances that are file uploads.
    
    This doesn't do any conversion, but it can detect empty upload
    fields (which appear like normal fields, but have no filename when
    no upload was given).
    """
    def deserialize(self, node, cstruct):
        if cstruct is colander.null:
            return cstruct
        if not isinstance(cstruct, cgi.FieldStorage) or \
            not getattr(cstruct, 'filename', None):
            raise colander.Invalid(
                node, 
                '%r is not a FieldStorage instance' % cstruct
            )
        return cstruct
    


class StringList(colander.String):
    def deserialize(self, node, cstruct):
        if cstruct is colander.null:
            return cstruct
        return [
            super(StringList, self).deserialize(node, x).strip() 
            for x in cstruct.split(", ") if x.strip() != ""
        ]
    

class HTMLString(colander.String):
    def deserialize(self, node, cstruct):
        if cstruct is colander.null:
            return cstruct
        text = super(HTMLString, self).deserialize(node, cstruct)
        try:
            soup = etree.fromstring(u"<div>%s</div>" % text)
            return etree.tostring(soup, encoding=unicode)[5:-6]
        except: # pragma: no cover
            soup = BeautifulSoup(text)
            return unicode(soup)
        
