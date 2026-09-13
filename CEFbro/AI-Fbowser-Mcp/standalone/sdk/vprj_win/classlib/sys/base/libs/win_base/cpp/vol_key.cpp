
// Copyright (C) Recursion Company. All rights reserved.

#include "../vol_base.h"

// 按键名称数组
static const TCHAR* cs_asKeyName [] =
{
     _T (""),
     _T ("LButton"),     // KYV_LBUTTON                 0x01
     _T ("RButton"),     // KYV_RBUTTON                 0x02

     _T ("Break"),       // KYV_BREAK                   0x03

     _T ("MButton"),     // KYV_MBUTTON                 0x04
     _T ("XButton1"),    // KYV_XBUTTON1                0x05
     _T ("XButton2"),    // KYV_XBUTTON2                0x06
     _T (""),

     _T ("Backspace"),   // KYV_BACKSPACE               0x08
     _T ("Tab"),         // KYV_TAB                     0x09

     _T (""),     _T (""),

     _T ("PadCenter"),   // KYV_PAD_CENTER              0x0C
     _T ("Enter"),       // KYV_ENTER                   0x0D

     _T (""),     _T (""),

     _T ("Shift"),       // KYV_SHIFT                   0x10
     _T ("Ctrl"),        // KYV_CTRL                    0x11
     _T ("Alt"),         // KYV_ALT                     0x12
     _T ("Pause"),       // KYV_PAUSE                   0x13
     _T ("CapsLock"),    // KYV_CAPS_LOCK               0x14

     _T ("KANA"),        // KYV_KANA                    0x15
     _T (""),
     _T ("JUNJA"),       // KYV_JUNJA                   0x17
     _T ("FINAL"),       // KYV_FINAL                   0x18
     _T ("HANJA"),       // KYV_HANJA                   0x19
     _T (""),
     _T ("ESC"),         // KYV_ESC                     0x1B

     _T ("Convert"),     // KYV_CONVERT                 0x1C
     _T ("Nonconvert"),  // KYV_NONCONVERT              0x1D
     _T ("Accept"),      // KYV_ACCEPT                  0x1E
     _T ("ModeChange"),  // KYV_MODECHANGE              0x1F

     _T ("Space"),       // KYV_SPACE                   0x20
     _T ("PageUp"),      // KYV_PAGEUP                  0x21
     _T ("PageDown"),    // KYV_PAGEDOWN                0x22
     _T ("End"),         // KYV_END                     0x23
     _T ("Home"),        // KYV_HOME                    0x24
     _T ("Left"),        // KYV_LEFT                    0x25
     _T ("Up"),          // KYV_UP                      0x26
     _T ("Right"),       // KYV_RIGHT                   0x27
     _T ("Down"),        // KYV_DOWN                    0x28
     _T ("Select"),      // KYV_SELECT                  0x29
     _T ("Print"),       // KYV_PRINT                   0x2A
     _T ("Execute"),     // KYV_EXECUTE                 0x2B
     _T ("Snapshot"),    // KYV_SNAPSHOT                0x2C
     _T ("Ins"),         // KYV_INS                     0x2D
     _T ("Del"),         // KYV_DEL                     0x2E
     _T ("Help"),        // KYV_HELP                    0x2F

     _T ("0"),           // KYV_0                       0x30
     _T ("1"),           // KYV_1                       0x31
     _T ("2"),           // KYV_2                       0x32
     _T ("3"),           // KYV_3                       0x33
     _T ("4"),           // KYV_4                       0x34
     _T ("5"),           // KYV_5                       0x35
     _T ("6"),           // KYV_6                       0x36
     _T ("7"),           // KYV_7                       0x37
     _T ("8"),           // KYV_8                       0x38
     _T ("9"),           // KYV_9                       0x39

     _T (""),     _T (""),     _T (""),     _T (""),
     _T (""),     _T (""),     _T (""),

     _T ("A"),           // KYV_A                       0x41
     _T ("B"),           // KYV_B                       0x42
     _T ("C"),           // KYV_C                       0x43
     _T ("D"),           // KYV_D                       0x44
     _T ("E"),           // KYV_E                       0x45
     _T ("F"),           // KYV_F                       0x46
     _T ("G"),           // KYV_G                       0x47
     _T ("H"),           // KYV_H                       0x48
     _T ("I"),           // KYV_I                       0x49
     _T ("J"),           // KYV_J                       0x4A
     _T ("K"),           // KYV_K                       0x4B
     _T ("L"),           // KYV_L                       0x4C
     _T ("M"),           // KYV_M                       0x4D
     _T ("N"),           // KYV_N                       0x4E
     _T ("O"),           // KYV_O                       0x4F
     _T ("P"),           // KYV_P                       0x50
     _T ("Q"),           // KYV_Q                       0x51
     _T ("R"),           // KYV_R                       0x52
     _T ("S"),           // KYV_S                       0x53
     _T ("T"),           // KYV_T                       0x54
     _T ("U"),           // KYV_U                       0x55
     _T ("V"),           // KYV_V                       0x56
     _T ("W"),           // KYV_W                       0x57
     _T ("X"),           // KYV_X                       0x58
     _T ("Y"),           // KYV_Y                       0x59
     _T ("Z"),           // KYV_Z                       0x5A

     _T ("LeftWin"),     // KYV_LWIN                    0x5B
     _T ("RightWin"),    // KYV_RWIN                    0x5C
     _T ("Apps"),        // KYV_APPS                    0x5D
     _T (""),
     _T ("Sleep"),       // KYV_SLEEP                   0x5F

     _T (""),     _T (""),     _T (""),     _T (""),
     _T (""),     _T (""),     _T (""),     _T (""),
     _T (""),     _T (""),

     _T ("PadMul"),      // KYV_PAD_MUL                 0x6A
     _T ("PadPlus"),     // KYV_PAD_PLUS                0x6B

     _T (""),     _T (""),     _T (""),     _T (""),

     _T ("F1"),          // KYV_F1                      0x70
     _T ("F2"),          // KYV_F2                      0x71
     _T ("F3"),          // KYV_F3                      0x72
     _T ("F4"),          // KYV_F4                      0x73
     _T ("F5"),          // KYV_F5                      0x74
     _T ("F6"),          // KYV_F6                      0x75
     _T ("F7"),          // KYV_F7                      0x76
     _T ("F8"),          // KYV_F8                      0x77
     _T ("F9"),          // KYV_F9                      0x78
     _T ("F10"),         // KYV_F10                     0x79
     _T ("F11"),         // KYV_F11                     0x7A
     _T ("F12"),         // KYV_F12                     0x7B
     _T ("F13"),         // KYV_F13                     0x7C
     _T ("F14"),         // KYV_F14                     0x7D
     _T ("F15"),         // KYV_F15                     0x7E
     _T ("F16"),         // KYV_F16                     0x7F
     _T ("F17"),         // KYV_F17                     0x80
     _T ("F18"),         // KYV_F18                     0x81
     _T ("F19"),         // KYV_F19                     0x82
     _T ("F20"),         // KYV_F20                     0x83
     _T ("F21"),         // KYV_F21                     0x84
     _T ("F22"),         // KYV_F22                     0x85
     _T ("F23"),         // KYV_F23                     0x86
     _T ("F24"),         // KYV_F24                     0x87

     _T (""),     _T (""),     _T (""),     _T (""),
     _T (""),     _T (""),     _T (""),     _T (""),

     _T ("NumLock"),     // KYV_NUM_LOCK                0x90
     _T ("ScrollLock"),  // KYV_SCROLL_LOCK             0x91
     _T ("Dictionary"),      // KYV_OEM_FJ_JISHO        0x92   // 'Dictionary' key
     _T ("UnregisterWord"),  // KYV_OEM_FJ_MASSHOU      0x93   // 'Unregister word' key
     _T ("RegisterWord"),    // KYV_OEM_FJ_TOUROKU      0x94   // 'Register word' key
     _T ("LeftOYAYUBI"),     // KYV_OEM_FJ_LOYA         0x95   // 'Left OYAYUBI' key
     _T ("RightOYAYUBI"),    // KYV_OEM_FJ_ROYA         0x96   // 'Right OYAYUBI' key

     _T (""),     _T (""),     _T (""),     _T (""),
     _T (""),     _T (""),     _T (""),     _T (""),
     _T (""),

     _T ("LeftShift"),          // KYV_LSHIFT                  0xA0
     _T ("RightShift"),         // KYV_RSHIFT                  0xA1
     _T ("LeftControl"),        // KYV_LCONTROL                0xA2
     _T ("RightControl"),       // KYV_RCONTROL                0xA3
     _T ("LeftMenu"),           // KYV_LMENU                   0xA4
     _T ("RightMenu"),          // KYV_RMENU                   0xA5
     _T ("BrowserBack"),        // KYV_BROWSER_BACK            0xA6
     _T ("BrowserForward"),     // KYV_BROWSER_FORWARD         0xA7
     _T ("BrowserRefresh"),     // KYV_BROWSER_REFRESH         0xA8
     _T ("BrowserStop"),        // KYV_BROWSER_STOP            0xA9
     _T ("BrowserSearch"),      // KYV_BROWSER_SEARCH          0xAA
     _T ("BrowserFavorites"),   // KYV_BROWSER_FAVORITES       0xAB
     _T ("BrowserHome"),        // KYV_BROWSER_HOME            0xAC
     _T ("VolumeMute"),         // KYV_VOLUME_MUTE             0xAD
     _T ("VolumeDown"),         // KYV_VOLUME_DOWN             0xAE
     _T ("VolumeUp"),           // KYV_VOLUME_UP               0xAF
     _T ("MediaNextTrack"),     // KYV_MEDIA_NEXT_TRACK        0xB0
     _T ("MediaPrevTrack") ,    // KYV_MEDIA_PREV_TRACK        0xB1
     _T ("MediaStop"),          // KYV_MEDIA_STOP              0xB2
     _T ("MediaPlayPause"),     // KYV_MEDIA_PLAY_PAUSE        0xB3
     _T ("LaunchMail"),         // KYV_LAUNCH_MAIL             0xB4
     _T ("LaunchMediaSelect"),  // KYV_LAUNCH_MEDIA_SELECT     0xB5
     _T ("LaunchApp1"),         // KYV_LAUNCH_APP1             0xB6
     _T ("LaunchApp2"),         // KYV_LAUNCH_APP2             0xB7

     _T (""),     _T (""),

     _T (";"),           // KYV_SEMICOLON               0xBA  // ';'
     _T ("="),           // KYV_EQUAL                   0xBB  // '='
     _T (","),           // KYV_COMMA                   0xBC  // ','
     _T ("-"),           // KYV_MINUS                   0xBD  // '-'
     _T ("."),           // KYV_DECIMAL                 0xBE  // '.'
     _T ("/"),           // KYV_DIV                     0xBF  // '/'
     _T ("`"),           // KYV_REVERSE_SINGLE_QUOTES   0xC0  // '`'

     _T (""),     _T (""),     _T (""),     _T (""),
     _T (""),     _T (""),     _T (""),     _T (""),
     _T (""),     _T (""),     _T (""),     _T (""),
     _T (""),     _T (""),     _T (""),     _T (""),
     _T (""),     _T (""),     _T (""),     _T (""),
     _T (""),     _T (""),     _T (""),     _T (""),
     _T (""),     _T (""),

     _T ("["),           // KYV_LEFT_SQUARE_BRACKETS    0xDB  // '['
     _T ("\\"),          // KYV_SLASH                   0xDC  // '\'
     _T ("]"),           // KYV_RIGHT_SQUARE_BRACKETS   0xDD  // ']'
     _T ("\'"),          // KYV_SINGLE_QUOTES           0xDE  // '''

     _T (""),     _T (""),

     _T ("OEM_AX"),         // KYV_OEM_AX                  0xE1  //  'AX' key on Japanese AX kbd
     _T ("OEM_102"),        // KYV_OEM_102                 0xE2  //  "<>" or "\|" on RT 102-key kbd.
     _T ("ICO_HELP"),       // KYV_ICO_HELP                0xE3  //  Help key on ICO
     _T ("ICO_00"),         // KYV_ICO_00                  0xE4  //  00 key on ICO
     _T ("PROCESSKEY"),     // KYV_PROCESSKEY              0xE5
     _T ("ICO_CLEAR"),      // KYV_ICO_CLEAR               0xE6
     _T ("PACKET"),         // KYV_PACKET                  0xE7

     _T (""),

     _T ("OEM_RESET"),      // KYV_OEM_RESET               0xE9
     _T ("OEM_JUMP"),       // KYV_OEM_JUMP                0xEA
     _T ("OEM_PA1"),        // KYV_OEM_PA1                 0xEB
     _T ("OEM_PA2"),        // KYV_OEM_PA2                 0xEC
     _T ("OEM_PA3"),        // KYV_OEM_PA3                 0xED
     _T ("OEM_WSCTRL"),     // KYV_OEM_WSCTRL              0xEE
     _T ("OEM_CUSEL"),      // KYV_OEM_CUSEL               0xEF
     _T ("OEM_ATTN"),       // KYV_OEM_ATTN                0xF0
     _T ("OEM_FINISH"),     // KYV_OEM_FINISH              0xF1
     _T ("OEM_COPY"),       // KYV_OEM_COPY                0xF2
     _T ("OEM_AUTO"),       // KYV_OEM_AUTO                0xF3
     _T ("OEM_ENLW"),       // KYV_OEM_ENLW                0xF4
     _T ("OEM_BACKTAB"),    // KYV_OEM_BACKTAB             0xF5
     _T ("ATTN"),           // KYV_ATTN                    0xF6
     _T ("CRSEL"),          // KYV_CRSEL                   0xF7
     _T ("EXSEL"),          // KYV_EXSEL                   0xF8
     _T ("EREOF"),          // KYV_EREOF                   0xF9
     _T ("PLAY"),           // KYV_PLAY                    0xFA
     _T ("ZOOM"),           // KYV_ZOOM                    0xFB
     _T ("NONAME"),         // KYV_NONAME                  0xFC
     _T ("PA1"),            // KYV_PA1                     0xFD
     _T ("OEM_CLEAR"),      // KYV_OEM_CLEAR               0xFE

     _T ("")
};

COMPILE_TIME_ASSERT (NUM_ELEMENTS_OF (cs_asKeyName) == 0x100);

//----------------------------------------------------------------------

// 按键所对应字符数组
static const TCHAR cs_acKeyChar [] =
{
     '\0',     '\0',     '\0',

     '\0',          // KYV_BREAK                   0x03

     '\0',     '\0',     '\0',     '\0',

     '\b',          // KYV_BACKSPACE               0x08
     '\t',          // KYV_TAB                     0x09

     '\0',     '\0',

     '\0',          // KYV_PAD_CENTER              0x0C
     '\r',          // KYV_ENTER                   0x0D

     '\0',     '\0',

     '\0',          // KYV_SHIFT                   0x10
     '\0',          // KYV_CTRL                    0x11
     '\0',          // KYV_ALT                     0x12
     '\0',          // KYV_PAUSE                   0x13
     '\0',          // KYV_CAPS_LOCK               0x14

     '\0',          // KYV_KANA                    0x15
     '\0',
     '\0',          // KYV_JUNJA                   0x17
     '\0',          // KYV_FINAL                   0x18
     '\0',          // KYV_HANJA                   0x19
     '\0',

     '\0',          // KYV_ESC                     0x1B

     '\0',          // KYV_CONVERT                 0x1C
     '\0',          // KYV_NONCONVERT              0x1D
     '\0',          // KYV_ACCEPT                  0x1E
     '\0',          // KYV_MODECHANGE              0x1F

     ' ',           // KYV_SPACE                   0x20
     '\0',          // KYV_PAGEUP                  0x21
     '\0',          // KYV_PAGEDOWN                0x22
     '\0',          // KYV_END                     0x23
     '\0',          // KYV_HOME                    0x24
     '\0',          // KYV_LEFT                    0x25
     '\0',          // KYV_UP                      0x26
     '\0',          // KYV_RIGHT                   0x27
     '\0',          // KYV_DOWN                    0x28
     '\0',          // KYV_SELECT                  0x29
     '\0',          // KYV_PRINT                   0x2A
     '\0',          // KYV_EXECUTE                 0x2B
     '\0',          // KYV_SNAPSHOT                0x2C
     '\0',          // KYV_INS                     0x2D
     '\0',          // KYV_DEL                     0x2E
     '\0',          // KYV_HELP                    0x2F

     '0',           // KYV_0                       0x30
     '1',           // KYV_1                       0x31
     '2',           // KYV_2                       0x32
     '3',           // KYV_3                       0x33
     '4',           // KYV_4                       0x34
     '5',           // KYV_5                       0x35
     '6',           // KYV_6                       0x36
     '7',           // KYV_7                       0x37
     '8',           // KYV_8                       0x38
     '9',           // KYV_9                       0x39

     '\0',     '\0',     '\0',     '\0',
     '\0',     '\0',     '\0',

     'A',           // KYV_A                       0x41
     'B',           // KYV_B                       0x42
     'C',           // KYV_C                       0x43
     'D',           // KYV_D                       0x44
     'E',           // KYV_E                       0x45
     'F',           // KYV_F                       0x46
     'G',           // KYV_G                       0x47
     'H',           // KYV_H                       0x48
     'I',           // KYV_I                       0x49
     'J',           // KYV_J                       0x4A
     'K',           // KYV_K                       0x4B
     'L',           // KYV_L                       0x4C
     'M',           // KYV_M                       0x4D
     'N',           // KYV_N                       0x4E
     'O',           // KYV_O                       0x4F
     'P',           // KYV_P                       0x50
     'Q',           // KYV_Q                       0x51
     'R',           // KYV_R                       0x52
     'S',           // KYV_S                       0x53
     'T',           // KYV_T                       0x54
     'U',           // KYV_U                       0x55
     'V',           // KYV_V                       0x56
     'W',           // KYV_W                       0x57
     'X',           // KYV_X                       0x58
     'Y',           // KYV_Y                       0x59
     'Z',           // KYV_Z                       0x5A

     '\0',          // KYV_LWIN                    0x5B
     '\0',          // KYV_RWIN                    0x5C
     '\0',          // KYV_APPS                    0x5D
     '\0',
     '\0',          // KYV_SLEEP                   0x5F

     '\0',     '\0',     '\0',     '\0',
     '\0',     '\0',     '\0',     '\0',
     '\0',     '\0',

     '*',           // KYV_PAD_MUL                 0x6A
     '+',           // KYV_PAD_PLUS                0x6B

     '\0',     '\0',     '\0',     '\0',

     '\0',          // KYV_F1                      0x70
     '\0',          // KYV_F2                      0x71
     '\0',          // KYV_F3                      0x72
     '\0',          // KYV_F4                      0x73
     '\0',          // KYV_F5                      0x74
     '\0',          // KYV_F6                      0x75
     '\0',          // KYV_F7                      0x76
     '\0',          // KYV_F8                      0x77
     '\0',          // KYV_F9                      0x78
     '\0',          // KYV_F10                     0x79
     '\0',          // KYV_F11                     0x7A
     '\0',          // KYV_F12                     0x7B
     '\0',          // KYV_F13                     0x7C
     '\0',          // KYV_F14                     0x7D
     '\0',          // KYV_F15                     0x7E
     '\0',          // KYV_F16                     0x7F
     '\0',          // KYV_F17                     0x80
     '\0',          // KYV_F18                     0x81
     '\0',          // KYV_F19                     0x82
     '\0',          // KYV_F20                     0x83
     '\0',          // KYV_F21                     0x84
     '\0',          // KYV_F22                     0x85
     '\0',          // KYV_F23                     0x86
     '\0',          // KYV_F24                     0x87

     '\0',     '\0',     '\0',     '\0',
     '\0',     '\0',     '\0',     '\0',

     '\0',          // KYV_NUM_LOCK                0x90
     '\0',          // KYV_SCROLL_LOCK             0x91

     '\0',     '\0',     '\0',     '\0',
     '\0',     '\0',     '\0',     '\0',
     '\0',     '\0',     '\0',     '\0',
     '\0',     '\0',     '\0',     '\0',
     '\0',     '\0',     '\0',     '\0',
     '\0',     '\0',     '\0',     '\0',
     '\0',     '\0',     '\0',     '\0',
     '\0',     '\0',     '\0',     '\0',
     '\0',     '\0',     '\0',     '\0',
     '\0',     '\0',     '\0',     '\0',

     ';',           // KYV_SEMICOLON               0xBA  // ';'
     '=',           // KYV_EQUAL                   0xBB  // '='
     ',',           // KYV_COMMA                   0xBC  // ','
     '-',           // KYV_MINUS                   0xBD  // '-'
     '.',           // KYV_DECIMAL                 0xBE  // '.'
     '/',           // KYV_DIV                     0xBF  // '/'
     '`',           // KYV_REVERSE_SINGLE_QUOTES   0xC0  // '`'

     '\0',     '\0',     '\0',     '\0',
     '\0',     '\0',     '\0',     '\0',
     '\0',     '\0',     '\0',     '\0',
     '\0',     '\0',     '\0',     '\0',
     '\0',     '\0',     '\0',     '\0',
     '\0',     '\0',     '\0',     '\0',
     '\0',     '\0',

     '[',           // KYV_LEFT_SQUARE_BRACKETS    0xDB  // '['
     '\\',          // KYV_SLASH                   0xDC  // '\'
     ']',           // KYV_RIGHT_SQUARE_BRACKETS   0xDD  // ']'
     '\'',          // KYV_SINGLE_QUOTES           0xDE  // '''

     '\0',     '\0',     '\0',     '\0',
     '\0',     '\0',     '\0',     '\0',
     '\0',     '\0',     '\0',     '\0',
     '\0',     '\0',     '\0',     '\0',
     '\0',     '\0',     '\0',     '\0',
     '\0',     '\0',     '\0',     '\0',
     '\0',     '\0',     '\0',     '\0',
     '\0',     '\0',     '\0',     '\0',
     '\0'
};

COMPILE_TIME_ASSERT (NUM_ELEMENTS_OF (cs_acKeyChar) == 0x100);

//----------------------------------------------------------------------

BOOL_P IsKeyCodeValid (const UINT_P upKeyCode)
{
    return (*cs_asKeyName [upKeyCode & 0xFF] != '\0');
}

const TCHAR* GetKeyName (const UINT_P upKeyCode, CVolString& strBuf)
{
    // 校验按键名称表的正确性
    ASSERT (cs_asKeyName [0x01] [0] == 'L' &&  // _T ("LButton")
            cs_asKeyName [0x03] [0] == 'B' &&  // _T ("Break")
            cs_asKeyName [0x08] [0] == 'B' &&  // _T ("Backspace")
            cs_asKeyName [0x0C] [0] == 'P' &&  // _T ("PadCenter")
            cs_asKeyName [0x10] [0] == 'S' &&  // _T ("Shift")
            cs_asKeyName [0x2D] [0] == 'I' &&  // _T ("Ins")
            cs_asKeyName [0x30] [0] == '0' &&  // _T ("0")
            cs_asKeyName [0x41] [0] == 'A' &&  // _T ("A")
            cs_asKeyName [0x6A] [0] == 'P' &&  // _T ("PadMul")
            cs_asKeyName [0x70] [0] == 'F' &&  // _T ("F1")
            cs_asKeyName [0x90] [0] == 'N' &&  // _T ("NumLock")
            cs_asKeyName [0xBA] [0] == ';' &&  // _T (";")
            cs_asKeyName [0xDB] [0] == '[');   // _T ("[")

    //----------------------------------------------------------------

    const UINT_P upBaseKeyCode = (upKeyCode & 0xFF);
    const TCHAR* psKeyName = cs_asKeyName [upBaseKeyCode];
    ASSERT (psKeyName != NULL);

    if (*psKeyName == '\0' ||  // 该按键不被支持?
            upBaseKeyCode == upKeyCode)  // 没有辅助键状态?
    {
        return psKeyName;
    }

    //----------------------------------------------------------------

    if ((upKeyCode & KYS_CONTROL) != 0)
        strBuf = _T ("Ctrl");
    else
        strBuf.Empty ();

    if ((upKeyCode & KYS_SHIFT) != 0)
        strBuf += (strBuf.IsEmpty () ? _T ("Shift") : _T ("+Shift"));

    if ((upKeyCode & KYS_ALT) != 0)
        strBuf += (strBuf.IsEmpty () ? _T ("Alt") : _T ("+Alt"));

    if (strBuf.IsEmpty () == FALSE)
        strBuf += '+';
    strBuf += psKeyName;

    return strBuf.GetText ();
}

UINT_P FindSpecNameKey (const TCHAR* szKeyPureName)
{
    if (IsEmptyStr (szKeyPureName) == FALSE)
    {
        for (INT_P npIndex = 0; npIndex < NUM_ELEMENTS_OF (cs_asKeyName); npIndex++)
        {
            if (_tcsicmp (szKeyPureName, cs_asKeyName [npIndex]) == 0)
                return (UINT_P)npIndex;
        }
    }

    return KYV_NULL;
}

TCHAR GetKeyAsciiChar (const UINT_P upKeyCode)
{
    if (upKeyCode >= (UINT_P)NUM_ELEMENTS_OF (cs_acKeyChar))
        return '\0';
    else
        return cs_acKeyChar [upKeyCode];
}

#ifdef _PF_WINDOWS

UINT_P GetKeyCodeFromMessage (const MSG* pMessage)
{
    ASSERT_R_DATA (pMessage);

    if (pMessage->message == WM_SYSKEYDOWN || pMessage->message == WM_KEYDOWN)
        return GetKeyCodeFromKeyMessage (pMessage);
    else
        return KYV_NULL;
}

UINT_P GetKeyCodeFromKeyMessageWParam (const WPARAM wKeyMsgParam)
{
    UINT_P upKeyCode = GetKeyCodeFromVirtualKey ((UINT_P)wKeyMsgParam);

    // 加上辅助键状态
    if (upKeyCode != KYV_NULL)
    {
        if (upKeyCode != KYV_CTRL && GetKeyState (VK_CONTROL) < 0)
            upKeyCode |= KYS_CONTROL;

        if (upKeyCode != KYV_SHIFT && GetKeyState (VK_SHIFT) < 0)
            upKeyCode |= KYS_SHIFT; 

        if (upKeyCode != KYV_ALT && GetKeyState (VK_MENU) < 0)
            upKeyCode |= KYS_ALT;
    }

    return upKeyCode;
}

UINT_P GetKeyCodeFromVirtualKey (const UINT_P upVirtualKey)
{
    UINT_P upKeyCode = (upVirtualKey & 0xFF);

    // 将小键盘键转换到大键盘
    if (upKeyCode >= 0x60 && upKeyCode <= 0x69)
    {
        upKeyCode = upKeyCode - 0x60 + KYV_0;
    }
    else if (upKeyCode == VK_SUBTRACT)
    {
        upKeyCode = KYV_MINUS;
    }
    else if (upKeyCode == VK_DECIMAL)
    {
        upKeyCode = KYV_DECIMAL;
    }
    else if (upKeyCode == VK_DIVIDE)
    {
        upKeyCode = KYV_DIV;
    }
    else
    {
        if (cs_asKeyName [upKeyCode][0] == '\0')  // 不被支持的按键?
            return KYV_NULL;
    }

    return upKeyCode;
}

UINT_P GetVirtualKeyFromKeyCode (const UINT_P upKeyCode)
{
    ASSERT ((upKeyCode & ~KYM_MASK) == 0);  // 必定不携带辅助键状态

    switch (upKeyCode)
    {
    case KYV_MINUS:
        return VK_SUBTRACT;

    case KYV_DECIMAL:
        return VK_DECIMAL;

    case KYV_DIV:
        return VK_DIVIDE;

    default:
        return upKeyCode;
    }
}

void GetAccelInfoFromKeyCode (const UINT_P upKeyCode, ACCEL* pAccelInfo)
{
    ASSERT_RW_DATA (pAccelInfo);

    // 获得辅助键状态
    UINT_P upVirt = (FVIRTKEY | FNOINVERT);
    if ((upKeyCode & KYS_CONTROL) != 0)
        upVirt |= FCONTROL;
    if ((upKeyCode & KYS_SHIFT) != 0)
        upVirt |= FSHIFT;
    if ((upKeyCode & KYS_ALT) != 0)
        upVirt |= FALT;

    pAccelInfo->fVirt = (BYTE)upVirt;
    pAccelInfo->key = (upKeyCode & KYM_MASK);
}

#endif
