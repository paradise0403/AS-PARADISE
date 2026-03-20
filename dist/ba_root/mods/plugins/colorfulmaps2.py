# This plugin developed for Bombsquad Server
# Custom lighting nodes and disco effects removed
# Original by: Lirik | Fixed by: Freak
import bascenev1 as bs
from bascenev1._map import Map

CONFIGS = {
    "IgnoreOnMaps": [],
}

def Map___init__(func):
    """
    Redefined method for bascenev1.Map.
    This wrapper ensures the map loads normally but skips 
    the addition of custom light nodes.
    """

    def wrapper(self, vr_overlay_offset=None):
        # Run the original map initialization (Standard Game Logic)
        func(self, vr_overlay_offset)

        name = self.getname()

        # Check if we should skip logic for this map
        if name in CONFIGS["IgnoreOnMaps"]:
            return

        # Light node creation, colors, and animations have been removed.
        # The map will now use its default engine lighting.

    return wrapper

# Apply the patch to the Map class
Map.__init__ = Map___init__(Map.__init__)