
import _bascenev1


def set_speed(x):
    try:
        activity = _bascenev1.get_foreground_host_activity()
        with activity.context:
            _bascenev1.set_game_speed(x)
    except:
        print("Error: feature available only in BCS server scripts.")
