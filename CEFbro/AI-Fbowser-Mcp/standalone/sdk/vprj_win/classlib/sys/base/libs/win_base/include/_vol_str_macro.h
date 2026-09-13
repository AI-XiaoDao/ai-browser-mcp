
// Copyright (C) Recursion Company. All rights reserved.

#undef _MY_STRING
#undef _MY_CONST_STRING
#undef _MY_STRING_WITH_HASH
#undef _MY_STRING_WITH_IHASH
#undef _MY_BUF_STRING
#undef _Q_COMPARE_CONST_TEXT
#undef _Q_COMPARE_I_CONST_TEXT

#undef _MYS_TCHAR
#undef _MYS_T
#undef _MYS_OTHER_CHAR

#undef _MYS_MEM_ADD_CHAR
#undef _MYS_MEM_REMOVE_END_ZERO_CHAR

#undef _MYS_STRCMP
#undef _MYS_STRICMP
#undef _MYS_STRNCMP
#undef _MYS_STRNICMP
#undef _MYS_STRLEN
#undef _MYS_SPRINTF
#undef _MYS_STRCHR
#undef _MYS_STRSTR
#undef _MYS_STRRCHR
#undef _MYS_VSCPRINTF
#undef _MYS_VSTPRINTF
#undef _MYS_TTOI
#undef _MYS_TTOF
#undef _MYS_STRCPY

//-------------------------------------------------------------------------

#ifdef _MY_WSTRING_IMPL

    #define _MY_STRING               _NAME_COMPILER_AGREED (CWString)
    #define _MY_CONST_STRING         CWConstString
    #define _MY_STRING_WITH_HASH     CWStringWithHash
    #define _MY_STRING_WITH_IHASH    CWStringWithIHash
    #define _MY_BUF_STRING           CWBufString
    #define _Q_COMPARE_CONST_TEXT    CQCompareConstWText
    #define _Q_COMPARE_I_CONST_TEXT  CQCompareIConstWText

    #define _MYS_TCHAR               WCHAR
    #define _MYS_T(t)                L ## t
    #define _MYS_OTHER_CHAR          U8CHAR

    #define _MYS_MEM_ADD_CHAR        AddWChar
    #define _MYS_MEM_REMOVE_END_ZERO_CHAR  RemoveEndZeroWChar

    #define _MYS_STRCMP              wcscmp
    #define _MYS_STRICMP             wcsicmp
    #define _MYS_STRNCMP             wcsncmp
    #define _MYS_STRNICMP            wcsnicmp
    #define _MYS_STRLEN              wcslen
    #define _MYS_SPRINTF             swprintf
    #define _MYS_STRCHR              wcschr
    #define _MYS_STRSTR              wcsstr
    #define _MYS_STRRCHR             wcsrchr
    #define _MYS_VSCPRINTF           _vscwprintf
    #define _MYS_VSTPRINTF           vswprintf
    #define _MYS_TTOI                _wtoi
    #define _MYS_TTOF                _wtof
    #define _MYS_STRCPY              wcscpy

#else

    #define _MY_STRING               CU8String
    #define _MY_CONST_STRING         CU8ConstString
    #define _MY_STRING_WITH_HASH     CU8StringWithHash
    #define _MY_STRING_WITH_IHASH    CU8StringWithIHash
    #define _MY_BUF_STRING           CU8BufString
    #define _Q_COMPARE_CONST_TEXT    CQCompareConstU8Text
    #define _Q_COMPARE_I_CONST_TEXT  CQCompareIConstU8Text

    #define _MYS_TCHAR               U8CHAR
    #define _MYS_T(t)                t
    #define _MYS_OTHER_CHAR          WCHAR

    #define _MYS_MEM_ADD_CHAR        AddU8Char
    #define _MYS_MEM_REMOVE_END_ZERO_CHAR  RemoveEndZeroU8Char

    #define _MYS_STRCMP              strcmp
    #define _MYS_STRICMP             stricmp
    #define _MYS_STRNCMP             strncmp
    #define _MYS_STRNICMP            strnicmp
    #define _MYS_STRLEN              strlen
    #define _MYS_SPRINTF             sprintf
    #define _MYS_STRCHR              strchr
    #define _MYS_STRSTR              strstr
    #define _MYS_STRRCHR             strrchr
    #define _MYS_VSCPRINTF           _vscprintf
    #define _MYS_VSTPRINTF           vsprintf
    #define _MYS_TTOI                atoi
    #define _MYS_TTOF                atof
    #define _MYS_STRCPY              strcpy

#endif
