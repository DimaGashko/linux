#include <X11/XKBlib.h>
#include <X11/keysym.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const char *layouts[] = {"us", "ru", "ua"};
static int recent[] = {0, 1, 2};
static int position;
static int cycling;
static int space_down;
static int grab_failed;
static KeyCode space;

static void remember(int group) {
    if (group < 0 || group >= 3) {
        return;
    }

    int index = 0;

    while (recent[index] != group) {
        index++;
    }

    for (; index > 0; index--) {
        recent[index] = recent[index - 1];
    }

    recent[0] = group;
}

static int current_group(Display *display) {
    XkbStateRec state;

    if (XkbGetState(display, XkbUseCoreKbd, &state) != Success) {
        fprintf(stderr, "Cannot read XKB state.\n");
        exit(1);
    }

    return state.group;
}

static int x_error(Display *display, XErrorEvent *event) {
    char message[256];
    XGetErrorText(display, event->error_code, message, sizeof(message));
    fprintf(stderr, "Keyboard shortcut error: %s\n", message);
    grab_failed = 1;
    return 0;
}

static void grab_shortcut(Display *display) {
    Window root = DefaultRootWindow(display);
    XModifierKeymap *modifiers = XGetModifierMapping(display);
    KeyCode num_lock = XKeysymToKeycode(display, XK_Num_Lock);
    unsigned int num_mask = 0;

    for (int modifier = 0; modifier < 8; modifier++) {
        for (int key = 0; key < modifiers->max_keypermod; key++) {
            if (num_lock && modifiers->modifiermap[modifier * modifiers->max_keypermod + key] == num_lock) {
                num_mask |= 1U << modifier;
            }
        }
    }

    XFreeModifiermap(modifiers);
    XUngrabKey(display, AnyKey, AnyModifier, root);
    space = XKeysymToKeycode(display, XK_space);

    for (unsigned int combination = 0; combination < 8; combination++) {
        unsigned int mask = Mod4Mask;

        if (combination & 1) {
            mask |= LockMask;
        }

        if (combination & 2) {
            mask |= num_mask;
        }

        if (combination & 4) {
            mask |= ShiftMask;
        }

        XGrabKey(display, space, mask, root, False, GrabModeAsync, GrabModeAsync);
    }

    XSync(display, False);

    if (grab_failed) {
        exit(1);
    }
}

int main(int argc, char **argv) {
    Display *display = XOpenDisplay(NULL);

    if (!display) {
        fprintf(stderr, "Cannot open the X11 display.\n");
        return 1;
    }

    int opcode, event_base, error_base;
    int major = XkbMajorVersion;
    int minor = XkbMinorVersion;

    if (!XkbQueryExtension(display, &opcode, &event_base, &error_base, &major, &minor)) {
        fprintf(stderr, "XKB is unavailable.\n");
        return 1;
    }

    if (argc == 3 && strcmp(argv[1], "--select") == 0) {
        for (int group = 0; group < 3; group++) {
            if (strcmp(argv[2], layouts[group]) == 0) {
                XkbLockGroup(display, XkbUseCoreKbd, group);
                XSync(display, False);
                XCloseDisplay(display);
                return 0;
            }
        }
    }

    if (argc != 1) {
        fprintf(stderr, "Usage: %s [--select us|ru|ua]\n", argv[0]);
        return 1;
    }

    Bool detectable = False;
    XkbSetDetectableAutoRepeat(display, True, &detectable);

    if (!detectable) {
        fprintf(stderr, "Detectable keyboard repeat is unavailable.\n");
        return 1;
    }

    XSetErrorHandler(x_error);
    XkbSelectEvents(display, XkbUseCoreKbd,
        XkbNewKeyboardNotifyMask | XkbMapNotifyMask,
        XkbNewKeyboardNotifyMask | XkbMapNotifyMask);
    XkbSelectEventDetails(display, XkbUseCoreKbd, XkbStateNotify,
        XkbAllStateComponentsMask, XkbModifierStateMask | XkbGroupStateMask);
    remember(current_group(display));
    grab_shortcut(display);
    fprintf(stderr, "Layout switcher ready (us,ru,ua).\n");

    for (;;) {
        XEvent event;
        XNextEvent(display, &event);

        if (event.type == KeyPress && event.xkey.keycode == space) {
            if (space_down) {
                continue;
            }

            space_down = 1;

            if (!cycling) {
                remember(current_group(display));
                cycling = 1;
                position = 0;
            }

            // Freeze the MRU order until Mod is released, like an Alt-Tab session.
            position = (position + ((event.xkey.state & ShiftMask) ? 2 : 1)) % 3;
            XkbLockGroup(display, XkbUseCoreKbd, recent[position]);
            XFlush(display);
        } else if (event.type == KeyRelease && event.xkey.keycode == space) {
            space_down = 0;
        } else if (event.type == event_base) {
            XkbEvent *keyboard = (XkbEvent *)&event;

            if (keyboard->any.xkb_type == XkbStateNotify) {
                if (cycling && !(keyboard->state.mods & Mod4Mask)) {
                    int selected = recent[position];
                    cycling = 0;
                    remember(selected);
                } else if (!cycling && (keyboard->state.changed & XkbGroupStateMask)) {
                    // Query the current state: queued notifications can predate our switch.
                    remember(current_group(display));
                }
            } else if (keyboard->any.xkb_type == XkbNewKeyboardNotify ||
                       keyboard->any.xkb_type == XkbMapNotify) {
                cycling = 0;
                space_down = 0;
                remember(current_group(display));
                grab_shortcut(display);
            }
        } else if (event.type == MappingNotify) {
            XRefreshKeyboardMapping(&event.xmapping);
            grab_shortcut(display);
        }
    }
}
