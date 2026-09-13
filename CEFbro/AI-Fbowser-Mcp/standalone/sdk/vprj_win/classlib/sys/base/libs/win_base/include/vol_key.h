
// Copyright (C) Recursion Company. All rights reserved.

#ifndef __VOL_KEY_H__
#define __VOL_KEY_H__

#define KYS_CONTROL                 (1 << 13)
#define KYS_ALT                     (1 << 14)
#define KYS_SHIFT                   (1 << 15)

#define KYM_MASK                    0xFF
#define KYV_NULL                    0

//----------------------------------------------------------------------

#define KYV_LBUTTON                 0x01
#define KYV_RBUTTON                 0x02
#define KYV_BREAK                   0x03
#define KYV_MBUTTON                 0x04
#define KYV_XBUTTON1                0x05
#define KYV_XBUTTON2                0x06

#define KYV_BACKSPACE               0x08
#define KYV_TAB                     0x09
#define KYV_PAD_CENTER              0x0C
#define KYV_ENTER                   0x0D

#define KYV_SHIFT                   0x10
#define KYV_CTRL                    0x11
#define KYV_ALT                     0x12
#define KYV_PAUSE                   0x13
#define KYV_CAPS_LOCK               0x14

#define KYV_KANA                    0x15
#define KYV_JUNJA                   0x17
#define KYV_FINAL                   0x18
#define KYV_HANJA                   0x19

#define KYV_ESC                     0x1B

#define KYV_CONVERT                 0x1C
#define KYV_NONCONVERT              0x1D
#define KYV_ACCEPT                  0x1E
#define KYV_MODECHANGE              0x1F

#define KYV_SPACE                   0x20
#define KYV_PAGEUP                  0x21
#define KYV_PAGEDOWN                0x22
#define KYV_END                     0x23
#define KYV_HOME                    0x24
#define KYV_LEFT                    0x25
#define KYV_UP                      0x26
#define KYV_RIGHT                   0x27
#define KYV_DOWN                    0x28
#define KYV_SELECT                  0x29
#define KYV_PRINT                   0x2A
#define KYV_EXECUTE                 0x2B
#define KYV_SNAPSHOT                0x2C
#define KYV_INS                     0x2D
#define KYV_DEL                     0x2E
#define KYV_HELP                    0x2F

#define KYV_0                       0x30
#define KYV_1                       0x31
#define KYV_2                       0x32
#define KYV_3                       0x33
#define KYV_4                       0x34
#define KYV_5                       0x35
#define KYV_6                       0x36
#define KYV_7                       0x37
#define KYV_8                       0x38
#define KYV_9                       0x39

#define KYV_A                       0x41
#define KYV_B                       0x42
#define KYV_C                       0x43
#define KYV_D                       0x44
#define KYV_E                       0x45
#define KYV_F                       0x46
#define KYV_G                       0x47
#define KYV_H                       0x48
#define KYV_I                       0x49
#define KYV_J                       0x4A
#define KYV_K                       0x4B
#define KYV_L                       0x4C
#define KYV_M                       0x4D
#define KYV_N                       0x4E
#define KYV_O                       0x4F
#define KYV_P                       0x50
#define KYV_Q                       0x51
#define KYV_R                       0x52
#define KYV_S                       0x53
#define KYV_T                       0x54
#define KYV_U                       0x55
#define KYV_V                       0x56
#define KYV_W                       0x57
#define KYV_X                       0x58
#define KYV_Y                       0x59
#define KYV_Z                       0x5A

#define KYV_LWIN                    0x5B
#define KYV_RWIN                    0x5C
#define KYV_APPS                    0x5D
#define KYV_SLEEP                   0x5F

#define KYV_PAD_MUL                 0x6A
#define KYV_PAD_PLUS                0x6B

#define KYV_F1                      0x70
#define KYV_F2                      0x71
#define KYV_F3                      0x72
#define KYV_F4                      0x73
#define KYV_F5                      0x74
#define KYV_F6                      0x75
#define KYV_F7                      0x76
#define KYV_F8                      0x77
#define KYV_F9                      0x78
#define KYV_F10                     0x79
#define KYV_F11                     0x7A
#define KYV_F12                     0x7B
#define KYV_F13                     0x7C
#define KYV_F14                     0x7D
#define KYV_F15                     0x7E
#define KYV_F16                     0x7F
#define KYV_F17                     0x80
#define KYV_F18                     0x81
#define KYV_F19                     0x82
#define KYV_F20                     0x83
#define KYV_F21                     0x84
#define KYV_F22                     0x85
#define KYV_F23                     0x86
#define KYV_F24                     0x87

#define KYV_NUM_LOCK                0x90
#define KYV_SCROLL_LOCK             0x91

#define KYV_OEM_FJ_JISHO            0x92   // 'Dictionary' key
#define KYV_OEM_FJ_MASSHOU          0x93   // 'Unregister word' key
#define KYV_OEM_FJ_TOUROKU          0x94   // 'Register word' key
#define KYV_OEM_FJ_LOYA             0x95   // 'Left OYAYUBI' key
#define KYV_OEM_FJ_ROYA             0x96   // 'Right OYAYUBI' key

#define KYV_LSHIFT                  0xA0
#define KYV_RSHIFT                  0xA1
#define KYV_LCONTROL                0xA2
#define KYV_RCONTROL                0xA3
#define KYV_LMENU                   0xA4
#define KYV_RMENU                   0xA5
#define KYV_BROWSER_BACK            0xA6
#define KYV_BROWSER_FORWARD         0xA7
#define KYV_BROWSER_REFRESH         0xA8
#define KYV_BROWSER_STOP            0xA9
#define KYV_BROWSER_SEARCH          0xAA
#define KYV_BROWSER_FAVORITES       0xAB
#define KYV_BROWSER_HOME            0xAC
#define KYV_VOLUME_MUTE             0xAD
#define KYV_VOLUME_DOWN             0xAE
#define KYV_VOLUME_UP               0xAF
#define KYV_MEDIA_NEXT_TRACK        0xB0
#define KYV_MEDIA_PREV_TRACK        0xB1
#define KYV_MEDIA_STOP              0xB2
#define KYV_MEDIA_PLAY_PAUSE        0xB3
#define KYV_LAUNCH_MAIL             0xB4
#define KYV_LAUNCH_MEDIA_SELECT     0xB5
#define KYV_LAUNCH_APP1             0xB6
#define KYV_LAUNCH_APP2             0xB7

#define KYV_SEMICOLON               0xBA  // ';'
#define KYV_EQUAL                   0xBB  // '='
#define KYV_COMMA                   0xBC  // ','
#define KYV_MINUS                   0xBD  // '-'
#define KYV_DECIMAL                 0xBE  // '.'
#define KYV_DIV                     0xBF  // '/'
#define KYV_REVERSE_SINGLE_QUOTES   0xC0  // '`'
#define KYV_LEFT_SQUARE_BRACKET     0xDB  // '['
#define KYV_SLASH                   0xDC  // '\'
#define KYV_RIGHT_SQUARE_BRACKET    0xDD  // ']'
#define KYV_SINGLE_QUOTES           0xDE  // '''

#define KYV_OEM_AX                  0xE1  //  'AX' key on Japanese AX kbd
#define KYV_OEM_102                 0xE2  //  "<>" or "\|" on RT 102-key kbd.
#define KYV_ICO_HELP                0xE3  //  Help key on ICO
#define KYV_ICO_00                  0xE4  //  00 key on ICO
#define KYV_PROCESSKEY              0xE5
#define KYV_ICO_CLEAR               0xE6
#define KYV_PACKET                  0xE7

#define KYV_OEM_RESET               0xE9
#define KYV_OEM_JUMP                0xEA
#define KYV_OEM_PA1                 0xEB
#define KYV_OEM_PA2                 0xEC
#define KYV_OEM_PA3                 0xED
#define KYV_OEM_WSCTRL              0xEE
#define KYV_OEM_CUSEL               0xEF
#define KYV_OEM_ATTN                0xF0
#define KYV_OEM_FINISH              0xF1
#define KYV_OEM_COPY                0xF2
#define KYV_OEM_AUTO                0xF3
#define KYV_OEM_ENLW                0xF4
#define KYV_OEM_BACKTAB             0xF5
#define KYV_ATTN                    0xF6
#define KYV_CRSEL                   0xF7
#define KYV_EXSEL                   0xF8
#define KYV_EREOF                   0xF9
#define KYV_PLAY                    0xFA
#define KYV_ZOOM                    0xFB
#define KYV_NONAME                  0xFC
#define KYV_PA1                     0xFD
#define KYV_OEM_CLEAR               0xFE

#define KYV_IMM_PROCESS             VK_PROCESSKEY  // 当输入法开启后,相关按键被其拦截后将改变为此代码.

//----------------------------------------------------------------------

// 返回upKeyCode键代码的名称,该键为KYV_NULL或者无效则返回空文本.
const TCHAR* GetKeyName (const UINT_P upKeyCode, CVolString& strBuf);

// 返回所指定名称按键对应的键代码,未找到返回KYV_NULL.
//   szKeyPureName: 所欲查找的按键名称,为基于不包括辅助键状态的按键代码调用GetKeyName所返回.
UINT_P FindSpecNameKey (const TCHAR* szKeyPureName);

// 返回upKeyCode是否不为KYV_NULL且有效
BOOL_P IsKeyCodeValid (const UINT_P upKeyCode);

// 返回upKeyCode键代码所对应的ASCII字符(不存在则返回字符'\0')
// 注意upKeyCode不能携带状态位(即KYS_xxx)
TCHAR GetKeyAsciiChar (const UINT_P upKeyCode);

#ifdef _PF_WINDOWS

// 如果pMessage消息为WM_SYSKEYDOWN/WM_KEYDOWN消息,则返回对应的按键代码,否则返回KYV_NULL.
// 所返回的按键代码: "KYV_xxx"宏值与"KYS_xxx"宏值的组合
UINT_P GetKeyCodeFromMessage (const MSG* pMessage);

// 当wKeyMsgParam消息为WM_SYSKEYDOWN/WM_KEYDOWN/WM_SYSKEYUP/WM_KEYUP消息的wParam参数时,返回对应的按键代码.
UINT_P GetKeyCodeFromKeyMessageWParam (const WPARAM wKeyMsgParam);

// 将虚拟按键码转换为火山按键码
UINT_P GetKeyCodeFromVirtualKey (const UINT_P upVirtualKey);

// 当pMessage消息为WM_SYSKEYDOWN/WM_KEYDOWN/WM_SYSKEYUP/WM_KEYUP消息时,返回对应的按键代码.
inline_ UINT_P GetKeyCodeFromKeyMessage (const MSG* pKeyMessage)
{
    ASSERT_R_DATA (pKeyMessage);
    ASSERT (pKeyMessage->message == WM_SYSKEYDOWN || pKeyMessage->message == WM_KEYDOWN ||
             pKeyMessage->message == WM_SYSKEYUP || pKeyMessage->message == WM_KEYUP);

    return GetKeyCodeFromKeyMessageWParam (pKeyMessage->wParam);
}

UINT_P GetVirtualKeyFromKeyCode (const UINT_P upKeyCode);

// 将对应upKeyCode键代码的快捷键信息填入pAccelInfo中(注意其cmd成员将不被更改)
void GetAccelInfoFromKeyCode (const UINT_P upKeyCode, ACCEL* pAccelInfo);

#endif

#endif
