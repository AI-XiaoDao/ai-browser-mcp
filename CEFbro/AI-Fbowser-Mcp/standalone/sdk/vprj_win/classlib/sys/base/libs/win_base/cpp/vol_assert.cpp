
// Copyright (C) Recursion Company. All rights reserved.

#include "../vol_base.h"

#ifdef _DEBUG

BOOL_P VolMsgAssert (const BOOL_P blpSucceed, const char* szTestCond, const char* szFileName, const INT_P npLineNO, const TCHAR* szErrorMessage)
{
    if (blpSucceed)
        return blpSucceed;

    CVolString strOutput;
#ifdef _PF_WINDOWS
    const BOOL_P blpDebuggerPresent = IsDebuggerPresent ();
    if (blpDebuggerPresent)
        strOutput.AddText (_T_VOL_DEBUG_OUT_STRING_LEADER _T ("\a"));
#endif
    CVolMem memBuf1, memBuf2;
    strOutput.AddFormatText (_T_RUNTIME_ASSERT_FAIL _T ("(\"%s\", ") _TF_NP _T ("): %s"),
            GetWideText (szFileName, memBuf1, NULL), npLineNO, GetWideText (szTestCond, memBuf2, NULL));

    if (IsEmptyStr (szErrorMessage) == FALSE)
    {
        strOutput.AddText (_T (", "));
        strOutput.AddText (szErrorMessage);
    }

    const TCHAR* szOutput = strOutput.GetText ();

#ifdef _PF_WINDOWS
    if (blpDebuggerPresent)
    {
        OutputDebugString (szOutput);
        __debugbreak ();
    }
    else
    {
        /* while (::OpenClipboard (NULL))
        {
            ::EmptyClipboard ();

            const INT_P npSize = (_tcslen (szOutput) + 1) * sizeof (TCHAR);
            HGLOBAL hMem = ::GlobalAlloc (GHND, (DWORD)npSize);
            if (hMem == NULL)
            {
                ::CloseClipboard ();
                break;
            }

            COPY_MEM ((LPBYTE)GlobalLock (hMem), szOutput, npSize);
            ::GlobalUnlock (hMem);

        #ifdef _UNICODE
            ::SetClipboardData (CF_UNICODETEXT, hMem);
        #else
            ::SetClipboardData (CF_TEXT, hMem);
        #endif
            ::CloseClipboard ();
            ::GlobalFree (hMem);  // We must not free the object until CloseClipboard is called.
            break;
        } */

        ::MessageBox (NULL, szOutput, _T_RUNTIME_ASSERT_FAIL, (MB_ICONERROR | MB_OK));
        assert (FALSE);
    }
#else
    PMSG0 (szOutput);
    __debugbreak ();
#endif

    return blpSucceed;
}

BOOL_P MAssert (const BOOL_P blpSucceed, const char* szTestCond, const char* szFileName, const INT_P npLineNO)
{
    return VolMsgAssert (blpSucceed, szTestCond, szFileName, npLineNO, _T (""));
}

#endif
