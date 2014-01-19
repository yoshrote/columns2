# encoding: utf-8
import zope.interface

class ICollectionContext(zope.interface.Interface):
    __parent__ = zope.interface.Attribute(
        """Instance of the parent collection or None"""
    )
    __name__ = zope.interface.Attribute("""The collection name""")
    def __getitem__(key):
        """ Retrieve member resource by ``key``
        If there are no matches then a KeyError is raise.
        ``key`` may be a slice, and if there are no matches an empty list 
        would be returned."""
    
    def __setitem__(key, value):
        """Updates an existing member resource and returns the updated 
        instance.  If no resource matches ``key`` then a KeyError is 
        raised."""
    
    def __delitem__(key):
        """Removes a member resource by ``key``
        If there are no matches a KeyError is raised."""
    
    def add(resource):
        """Created a new member resource and returns the persistent 
        instance"""
    
    def discard(key):
        """ Removes a member resource by ``key``
        If there are no matches no errors are raise."""
    
    def remove(key):
        """ Removes a member resource by ``key``
        If there are no matches a KeyError is raise."""
    
    def clear():
        """ Removes all member resources"""
    
    def __len__():
        """Returns the number of resources in the collection"""
    
    def __contains__(key):
        """Checks if a member resource with the key ``key`` exists in the 
        collection"""
    
    def get(key, default=None):
        """ Retrieve member resource by ``key``
        If there are no matches a default value is returned"""
    
    def to_json():
        """Returns the collection in a JSON formatable form or raises a
        NotImplementedError"""
    

class IMemberContext(zope.interface.Interface):
    __name__ = zope.interface.Attribute("""The member name""")
    def get_key():
        """Retrieves the primary key in a form suitable for traversal"""
    
    def set_key(key):
        """Sets the primary key from a form suitable for traversal"""
    
    def update_from_values(values):
        """Updates a member resource from a dictionary ``values``"""
    
    def build_from_values(values):
        """Creates a non-persistent member resource from a dictionary 
        ``values``"""
    

class IResourceView(zope.interface.Interface):
    # collection views
    def index():
        "Display a list of resources in a collection"
    
    def create():
        "Create a new resource"
    
    def new():
        "Display a new instance of a resource type"
    
    # member views
    def show():
        "Display a list of resources in a collection"
    
    def update():
        "Update a resources in a collection"
    
    def delete():
        "Delete a resources from a collection"
    

