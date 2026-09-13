
// Copyright (C) Recursion Company. All rights reserved.

#include "../vol_base.h"

void strncpy_z (U8CHAR* dest, const U8CHAR* source, const INT_P npNumChars)
{
    ASSERT (npNumChars >= 0);
    ASSERT_RW_ADR (dest, (npNumChars + 1) * sizeof (U8CHAR));

    if (npNumChars < 0)
        return;
    ASSERT (IsBadReadPtr (source, npNumChars) == FALSE);

    for (INT_P npIndex = 0; npIndex < npNumChars; npIndex++)
    {
        const U8CHAR ch = *source;
        if (ch == '\0')
            break;

        *dest++ = ch;
        source++;
    }

    *dest = '\0';
}

void wcsncpy_z (WCHAR* dest, const WCHAR* source, const INT_P npNumChars)
{
    ASSERT (npNumChars >= 0);
    ASSERT_RW_ADR (dest, (npNumChars + 1) * sizeof (WCHAR));

    if (npNumChars < 0)
        return;
    ASSERT (IsBadReadPtr (source, npNumChars) == FALSE);

    for (INT_P npIndex = 0; npIndex < npNumChars; npIndex++)
    {
        const WCHAR ch = *source;
        if (ch == '\0')
            break;

        *dest++ = ch;
        source++;
    }

    *dest = '\0';
}

BOOL_P SplitString2 (const TCHAR* szText, const TCHAR chDelimit, const BOOL_P blpTrimAll, CVolString& strLeft, CVolString& strRight)
{
    ASSERT_R_STR (szText);

    if (IsEmptyStr (szText))
        return FALSE;

    const TCHAR* ps = _tcschr (szText, chDelimit);
    if (ps == NULL)
        return FALSE;

    if (strLeft.IsNullObject () == FALSE)
    {
        strLeft.SetText (szText, ps - szText);
        if (blpTrimAll)
            strLeft.TrimAll ();
    }

    if (strRight.IsNullObject () == FALSE)
    {
        strRight.SetText (ps + 1);
        if (blpTrimAll)
            strRight.TrimAll ();
    }

    return TRUE;
}

BOOL_P SplitSubString2 (const TCHAR* szText, const TCHAR* szDelimitText, const BOOL_P blpTrimAll, CVolString& strLeft, CVolString& strRight)
{
    ASSERT_R_STR (szText);
    ASSERT_R_STR (szDelimitText);

    if (IsEmptyStr (szText))
        return FALSE;

    if (IsEmptyStr (szDelimitText))
    {
        if (strLeft.IsNullObject () == FALSE)
            strLeft.SetText (szText);

        if (strRight.IsNullObject () == FALSE)
            strRight.Empty ();
    }
    else
    {
        const TCHAR* ps = _tcsstr (szText, szDelimitText);
        if (ps == NULL)
            return FALSE;

        if (strLeft.IsNullObject () == FALSE)
        {
            strLeft.SetText (szText, ps - szText);
            if (blpTrimAll)
                strLeft.TrimAll ();
        }

        if (strRight.IsNullObject () == FALSE)
        {
            strRight.SetText (ps + _tcslen (szDelimitText));
            if (blpTrimAll)
                strRight.TrimAll ();
        }
    }

    return TRUE;
}

INT_P SplitStrings (const TCHAR* szText, CMStringArray& strary, const TCHAR chDelimit,
        const BOOL_P blpTrimAll, const BOOL_P blpIgnoreEmptyStr)
{
    TCHAR buf [2];
    buf [0] = chDelimit;
    buf [1] = '\0';

    return SplitStringsSupportManyDelimitChar (szText, strary, buf, blpTrimAll, blpIgnoreEmptyStr);
}

INT_P SplitStringsSupportManyDelimitChar (const TCHAR* szText, CMStringArray& strary, const TCHAR* szDelimit,
        const BOOL_P blpTrimAll, const BOOL_P blpIgnoreEmptyStr)
{
    ASSERT_R_STR (szText);
    ASSERT_R_STR (szDelimit);

    strary.RemoveAll ();

    CVolString str;
    const TCHAR* psBegin = szText;

    while (IsEmptyStr (psBegin) == FALSE)
    {
        const TCHAR* psFound = NULL;
        const TCHAR* psFind = psBegin;

        do
        {
            const TCHAR chFind = *psFind;
            if (chFind == '\0')
                break;

            const TCHAR* ps = szDelimit;
            while (TRUE)
            {
                const TCHAR chDelimit = *ps++;
                if (chDelimit == '\0')
                    break;

                if (chDelimit == chFind)
                {
                    psFound = psFind;
                    break;
                }
            }

            psFind++;
        }
        while (psFound == NULL);

        //-------------------------------------------------------------------------

        if (psFound != NULL)
        {
            str.SetText (psBegin, psFound - psBegin);
            psBegin = psFound + 1;
        }
        else
        {
            str.SetText (psBegin);
            psBegin = NULL;
        }

        if (blpTrimAll)  // 是否清除首尾空白?
        {
            str.TrimAll ();

            // 处理忽略所有空白文本
            if (blpIgnoreEmptyStr && str.IsEmpty ())
                continue;
        }
        else if (blpIgnoreEmptyStr)  // 忽略所有空白文本?
        {
            if (*SkipSpaces (str.GetText ()) == '\0')  // 全部为空白字符?
                continue;
        }

        strary.Add (str.GetText ());

        // 处理分隔符在文本尾部的情况
        if (blpIgnoreEmptyStr == FALSE &&  // 不忽略所有空白文本?
                psBegin != NULL &&  // 前面找到了分隔符?
                *psBegin == '\0')  // 该分隔符处于文本结束位置?
        {
            strary.Add (_T (""));
            break;
        }
    }

    return strary.GetCount ();
}

INT_P SplitSubStrings (const TCHAR* szText, CMStringArray& strary, const TCHAR* szDelimitText,
        const BOOL_P blpTrimAll, const BOOL_P blpIgnoreEmptyStr)
{
    ASSERT_R_STR (szText);
    ASSERT_R_STR (szDelimitText);

    strary.RemoveAll ();

    if (IsEmptyStr (szDelimitText))
    {
        strary.Add (szText);
    }
    else
    {
        const INT_P npLen = _tcslen (szDelimitText);

        CVolString str;
        const TCHAR* psBegin = szText;

        while (IsEmptyStr (psBegin) == FALSE)
        {
            const TCHAR* psFound = _tcsstr (psBegin, szDelimitText);

            if (psFound != NULL)
            {
                str.SetText (psBegin, psFound - psBegin);
                psBegin = psFound + npLen;
            }
            else
            {
                str.SetText (psBegin);
                psBegin = NULL;
            }

            if (blpTrimAll)  // 是否清除首尾空白?
            {
                str.TrimAll ();

                // 处理忽略所有空白文本
                if (blpIgnoreEmptyStr && str.IsEmpty ())
                    continue;
            }
            else if (blpIgnoreEmptyStr)  // 忽略所有空白文本?
            {
                if (*SkipSpaces (str.GetText ()) == '\0')  // 全部为空白字符?
                    continue;
            }

            strary.Add (str.GetText ());

            // 处理分隔符在文本尾部的情况
            if (blpIgnoreEmptyStr == FALSE &&  // 不忽略所有空白文本?
                    psBegin != NULL &&  // 前面找到了分隔符?
                    *psBegin == '\0')  // 该分隔符处于文本结束位置?
            {
                strary.Add (_T (""));
                break;
            }
        }
    }

    return strary.GetCount ();
}

INT_P SplitIntegers (const TCHAR* szText, CMArray<INT>& nary, const TCHAR chDelimit)
{
    ASSERT_R_STR (szText);

    nary.RemoveAll ();

    CVolString str;
    const TCHAR* psBegin = szText;

    while (IsEmptyStr (psBegin) == FALSE)
    {
        const TCHAR* ps = _tcschr (psBegin, chDelimit);

        if (ps != NULL)
        {
            str.SetText (psBegin, ps - psBegin);
            psBegin = ps + 1;
        }
        else
        {
            str.SetText (psBegin);
            psBegin = NULL;
        }
        str.TrimAll ();

        if (str.IsEmpty () == FALSE)
            nary.Add (_ttoi (str.GetText ()));
        else
            nary.Add (0);

        // 处理分隔符在文本尾部的情况
        if (psBegin != NULL &&  // 前面找到了分隔符?
                *psBegin == '\0')  // 该分隔符处于文本结束位置?
        {
            nary.Add (0);
            break;
        }
    }

    return nary.GetCount ();
}

INT_P SplitDoubles (const TCHAR* szText, CMArray<DOUBLE>& dbary, const TCHAR chDelimit)
{
    ASSERT_R_STR (szText);

    dbary.RemoveAll ();

    CVolString str;
    const TCHAR* psBegin = szText;

    while (IsEmptyStr (psBegin) == FALSE)
    {
        const TCHAR* ps = _tcschr (psBegin, chDelimit);

        if (ps != NULL)
        {
            str.SetText (psBegin, ps - psBegin);
            psBegin = ps + 1;
        }
        else
        {
            str.SetText (psBegin);
            psBegin = NULL;
        }
        str.TrimAll ();

        if (str.IsEmpty () == FALSE)
            dbary.Add (_tstof (str.GetText ()));
        else
            dbary.Add (0.0);

        // 处理分隔符在文本尾部的情况
        if (psBegin != NULL &&  // 前面找到了分隔符?
                *psBegin == '\0')  // 该分隔符处于文本结束位置?
        {
            dbary.Add (0.0);
            break;
        }
    }

    return dbary.GetCount ();
}

const TCHAR* ComboStrings (const CMStringArray& strary, CVolString& strResult, const TCHAR chDelimit, const BOOL_P blpInsertSpace)
{
    strResult.Empty ();

    const INT_P npCount = strary.GetCount ();
    for (INT_P npIndex = 0; npIndex < npCount; npIndex++)
    {
        if (npIndex > 0)
        {
            strResult.AddChar (chDelimit);
            if (blpInsertSpace)  // 需要插入空白字符?
                strResult.AddChar (' ');
        }

        strResult += strary [npIndex];
    }

    return strResult.GetText ();
}

//-------------------------------------------------------------

U8CHAR* ConvertText (const WCHAR* wszText, const INT_P npLen, CVolMem& memBuf)
{
    if (wszText == NULL || npLen <= 0)
        return NULL;
    ASSERT_R_STR2 (wszText, npLen);

    ::WStrToUtf8 (wszText, npLen, memBuf, NULL, NULL, TRUE);
    return (U8CHAR*)memBuf.GetPtr ();
}

WCHAR* ConvertText (const U8CHAR* szText, const INT_P npLen, CVolMem& memBuf)
{
    if (szText == NULL || npLen <= 0)
        return NULL;
    ASSERT_R_STR2 (szText, npLen);

    ::Utf8ToWStr (szText, npLen, memBuf, NULL, NULL, TRUE);
    return (WCHAR*)memBuf.GetPtr ();
}

//-------------------------------------------------------------

/* UTF8代码转换表:
+-------------------------+----------+-------------+----------+----------------------------------+
|    UNICODE              |  bit数   |  UTF-8      |  byte数  |   备注                           |
+-------------------------+----------+-------------+----------+----------------------------------+
|  0000 0000 ~ 0000 007F  |   0~7    |  0XXX XXXX  |    1     |                                  |
+-------------------------+----------+-------------+----------+----------------------------------+
|  0000 0080 ~ 0000 07FF  |   8~11   |  110X XXXX  |    2     |                                  |
|                         |          |  10XX XXXX  |          |                                  |
+-------------------------+----------+-------------+----------+----------------------------------+
|                         |          |  1110 XXXX  |          |                                  |
|  0000 0800 ~ 0000 FFFF  |   12~16  |  10XX XXXX  |    3     |  基本定义范围：0 ~ FFFF          |
|                         |          |  10XX XXXX  |          |                                  |
+-------------------------+----------+-------------+----------+----------------------------------+
|                         |          |  1111 0XXX  |          |                                  |
|  0001 0000 ~ 001F FFFF  |   17~21  |  10XX XXXX  |    4     |  Unicode6.1定义范围：0 ~ 10 FFFF |
|                         |          |  10XX XXXX  |          |                                  |
|                         |          |  10XX XXXX  |          |                                  |
+-------------------------+----------+-------------+----------+----------------------------------+
|                         |          |  1111 10XX  |          |                                  |
|                         |          |  10XX XXXX  |          |                                  |
|  0020 0000 ~ 03FF FFFF  |   22~26  |  10XX XXXX  |    5     |                                  |
|                         |          |  10XX XXXX  |          |                                  |
|                         |          |  10XX XXXX  |          |                                  |
+-------------------------+----------+-------------+----------+----------------------------------+
|                         |          |  1111 110X  |          |                                  |
|                         |          |  10XX XXXX  |          |                                  |
|  0400 0000 ~ 7FFF FFFF  |   27~31  |  10XX XXXX  |    6     |                                  |
|                         |          |  10XX XXXX  |          |                                  |
|                         |          |  10XX XXXX  |          |                                  |
|                         |          |  10XX XXXX  |          |                                  |
+-------------------------+----------+-------------+----------+----------------------------------+
*/

//!! 注意: 结果必须放入memBuf中,因为可能会对返回结果文本进行修改.
U8CHAR* WStrToUtf8 (const WCHAR* pwsText, INT_P npLength, CVolMem& memBuf,
        INT_P* pnpUtf8StrLength, BOOL_P* pblpFoundInvalidChar, const BOOL_P blpCutBufSpace)
{
    ASSERT (npLength >= -1);
    ASSERT_R_STR2_NEG1 (pwsText, npLength);
    ASSERT_RW_DATA_OR_NULL (pnpUtf8StrLength);
    ASSERT_RW_DATA_OR_NULL (pblpFoundInvalidChar);

    if (npLength == -1)  // 自行获取文本长度?
        npLength = wcslen (pwsText);

    if (pnpUtf8StrLength != NULL)
    {
        ASSERT_RW_DATA (pnpUtf8StrLength);
        *pnpUtf8StrLength = 0;
    }

    if (pblpFoundInvalidChar != NULL)
    {
        ASSERT_RW_DATA (pblpFoundInvalidChar);
        *pblpFoundInvalidChar = FALSE;
    }

    if (npLength > 0)
    {
        INT_P npBufLen = ::WideCharToMultiByte (CP_UTF8, 0, pwsText, (INT)npLength, NULL, 0, NULL, NULL);

        CHAR* psBuf = (CHAR*)memBuf.Alloc ((npBufLen + 1) * (INT_P)sizeof (CHAR));
        npBufLen = ::WideCharToMultiByte (CP_UTF8, 0, pwsText, (INT)npLength, psBuf, (INT)npBufLen, NULL, NULL);

        if (npBufLen > 0)  // 转换成功?
        {
            ASSERT (npBufLen + 1 <= memBuf.GetSize () / (INT_P)sizeof (CHAR));

            psBuf [npBufLen] = '\0';

            if (pnpUtf8StrLength != NULL)
                *pnpUtf8StrLength = npBufLen;
            return psBuf;
        }
    }

    memBuf.Empty ();
    memBuf.AddU8Char ('\0');
    return (U8CHAR*)memBuf.GetPtr ();

/*
    #define _LEAD_SURROGATE_MIN   0xd800u
    #define _LEAD_SURROGATE_MAX   0xdbffu
    #define _TRAIL_SURROGATE_MIN  0xdc00u
    #define _TRAIL_SURROGATE_MAX  0xdfffu
    #define _SURROGATE_OFFSET     (0x10000u - (_LEAD_SURROGATE_MIN << 10) - _TRAIL_SURROGATE_MIN)
    #define _CODE_POINT_MAX       0x0010ffffu  // Maximum valid value for a Unicode code point

    //-------------------------------------------------

    if (npLength == -1)  // 自行获取文本长度?
        npLength = wcslen (pwsText);

    const WCHAR* pwsTextEnd = pwsText + npLength;  // 获得文本尾指针

    BOOL_P blpFoundInvalidChar = FALSE;  // 用作记录是否找到了无效字符
    BYTE* pbResult = (BYTE*)memBuf.Alloc (npLength * 4 + 1);  // 分配足够尺寸的缓冲区

    while (pwsText < pwsTextEnd)
    {
        UINT_P upChar = (UINT_P)*pwsText;
        if (upChar == '\0')
            break;
        pwsText++;

        if (upChar >= _LEAD_SURROGATE_MIN && upChar <= _LEAD_SURROGATE_MAX)
        {
            if (pwsText >= pwsTextEnd)
            {
                blpFoundInvalidChar = TRUE;  // 标记找到了无效字符
                break;
            }

            const DWORD dwTrailSurrogate = ((DWORD)*pwsText & 0xFFFF);
            pwsText++;

            if (dwTrailSurrogate >= _TRAIL_SURROGATE_MIN && dwTrailSurrogate <= _TRAIL_SURROGATE_MAX)
            {
                upChar = (upChar << 10) + dwTrailSurrogate + _SURROGATE_OFFSET;
            }
            else
            {
                blpFoundInvalidChar = TRUE;  // 标记找到了无效字符
                continue;
            }
        }
        // Lone trail surrogate
        else if (upChar >= _TRAIL_SURROGATE_MIN && upChar <= _TRAIL_SURROGATE_MAX)
        {
            blpFoundInvalidChar = TRUE;  // 标记找到了无效字符
            continue;
        }

        if (upChar > _CODE_POINT_MAX || (upChar >= _LEAD_SURROGATE_MIN && upChar <= _TRAIL_SURROGATE_MAX))
        {
            blpFoundInvalidChar = TRUE;  // 标记找到了无效字符
            continue;
        }

        //-------------------------------------------------

        if (upChar < 0x80)  // one octet
        {
            *pbResult++ = (BYTE)(upChar);
        }
        else if (upChar < 0x800)  // two octets
        {
            *pbResult++ = (BYTE)((upChar >> 6)   | 0xc0);
            *pbResult++ = (BYTE)((upChar & 0x3f) | 0x80);
        }
        else if (upChar < 0x10000)  // three octets
        {
            *pbResult++ = (BYTE)((upChar >> 12)          | 0xe0);
            *pbResult++ = (BYTE)(((upChar >> 6) & 0x3f)  | 0x80);
            *pbResult++ = (BYTE)((upChar & 0x3f)         | 0x80);
        }
        else  // four octets
        {
            *pbResult++ = (BYTE)((upChar >> 18)          | 0xf0);
            *pbResult++ = (BYTE)(((upChar >> 12) & 0x3f) | 0x80);
            *pbResult++ = (BYTE)(((upChar >> 6) & 0x3f)  | 0x80);
            *pbResult++ = (BYTE)((upChar & 0x3f)         | 0x80);
        }
    }

    ASSERT (memBuf.IsInside (pbResult, sizeof (BYTE)));  // 必定在缓冲区内部
    *pbResult = '\0';  // 加入结束0字符

    //-------------------------------------------------

    // 记录是否找到了无效字符
    if (pblpFoundInvalidChar != NULL)
        *pblpFoundInvalidChar = blpFoundInvalidChar;

    // 返回转换后文本的长度
    if (pnpUtf8StrLength != NULL)
        *pnpUtf8StrLength = pbResult - memBuf.GetPtr ();

    //!! 注意: 结果必须放入memBuf中,因为可能会对返回结果文本进行修改.
    if (blpCutBufSpace)
        return (U8CHAR*)memBuf.Realloc (pbResult + 1 - memBuf.GetPtr ());  // 返回转换结果文本并释放多余空间
    else
        return (U8CHAR*)memBuf.GetPtr (); */
}

static const BYTE c_btLead1     = 0xC0;  // 110xxxxx
static const BYTE c_btLead1Mask = 0x1F;  // 00011111
static const BYTE c_btLead2     = 0xE0;  // 1110xxxx
static const BYTE c_btLead2Mask = 0x0F;  // 00001111
static const BYTE c_btLead3     = 0xF0;  // 11110xxx
static const BYTE c_btLead3Mask = 0x07;  // 00000111
static const BYTE c_btLead4     = 0xF8;  // 111110xx
static const BYTE c_btLead4Mask = 0x03;  // 00000011
static const BYTE c_btLead5     = 0xFC;  // 1111110x
static const BYTE c_btLead5Mask = 0x01;  // 00000001
static const BYTE c_btCont      = 0x80;  // 10xxxxxx
static const BYTE c_btContMask  = 0x3F;  // 00111111

INT_P GetUTF8CharBytes (const BYTE btU8CharLeader)
{
    if ((btU8CharLeader & 0x80) == 0)
        return (btU8CharLeader == '\0' ? -1 : 1);
    
    if ((btU8CharLeader & ~c_btLead1Mask) == c_btLead1)
        return 2;

    if ((btU8CharLeader & ~c_btLead2Mask) == c_btLead2)
        return 3;

    if ((btU8CharLeader & ~c_btLead3Mask) == c_btLead3)
        return 4;

    if ((btU8CharLeader & ~c_btLead4Mask) == c_btLead4)
        return 5;

    if ((btU8CharLeader & ~c_btLead5Mask) == c_btLead5)
        return 6;

    return -1;  // 非法UTF8字符前缀
}

//!! 注意: 结果必须放入memBuf中,因为可能会对返回结果文本进行修改.
WCHAR* Utf8ToWStr (const U8CHAR* psText, INT_P npLength, CVolMem& memBuf,
        INT_P* pnpWStrLength, BOOL_P* pblpFoundInvalidChar, const BOOL_P blpCutBufSpace)
{
    ASSERT (npLength >= -1);
    ASSERT_R_STR2_NEG1 (psText, npLength);
    ASSERT_RW_DATA_OR_NULL (pnpWStrLength);
    ASSERT_RW_DATA_OR_NULL (pblpFoundInvalidChar);

    if (npLength == -1)
        npLength = strlen (psText);

    if (pnpWStrLength != NULL)
    {
        ASSERT_RW_DATA (pnpWStrLength);
        *pnpWStrLength = 0;
    }

    if (pblpFoundInvalidChar != NULL)
    {
        ASSERT_RW_DATA (pblpFoundInvalidChar);
        *pblpFoundInvalidChar = FALSE;
    }

    if (npLength > 0)
    {
        INT_P npBufLen = ::MultiByteToWideChar (CP_UTF8, 0, psText, (INT)npLength, NULL, 0);

        WCHAR* pwsBuf = (WCHAR*)memBuf.Alloc ((npBufLen + 1) * (INT_P)sizeof (WCHAR));
        npBufLen = ::MultiByteToWideChar (CP_UTF8, 0, psText, (INT)npLength, pwsBuf, (INT)npBufLen);

        if (npBufLen > 0)  // 转换成功?
        {
            ASSERT (npBufLen + 1 <= memBuf.GetSize () / (INT_P)sizeof (WCHAR));

            pwsBuf [npBufLen] = '\0';

            if (pnpWStrLength != NULL)
                *pnpWStrLength = npBufLen;
            return pwsBuf;
        }
    }

    memBuf.Empty ();
    memBuf.AddWChar ('\0');
    return (WCHAR*)memBuf.GetPtr ();

/*
    if (npLength == -1)
        npLength = strlen (psText);

    const U8CHAR* psTextEnd = psText + npLength;

    BOOL_P blpFoundInvalidChar = FALSE;
    WCHAR* pwcResult = (WCHAR*)memBuf.Alloc (sizeof (WCHAR) * (npLength + 1));  // 分配足够尺寸的缓冲区

    while (psText < psTextEnd)
    {
        BYTE btU8Char = (BYTE)*psText++;
        if (btU8Char == '\0')
            break;

        // 获取当前UTF8字符的字节数
        const INT_P npCharLen = GetUTF8CharBytes (btU8Char);

        if (npCharLen == -1)
        {
            // 非法UTF8字符前缀
            blpFoundInvalidChar = TRUE;
            break;
        }

        //------------------------------------------------  获得当前UTF8字符对应的Unicode32字符

        DWORD dwUTF32Char;

        if (npCharLen == 1)  // 当前字符仅有一个字节?
        {
            dwUTF32Char = btU8Char;
        }
        else
        {
            switch (npCharLen)
            {
            case 6:
                dwUTF32Char = btU8Char & c_btLead5Mask;
                break;
            case 5:
                dwUTF32Char = btU8Char & c_btLead4Mask;
                break;
            case 4:
                dwUTF32Char = btU8Char & c_btLead3Mask;
                break;
            case 3:
                dwUTF32Char = btU8Char & c_btLead2Mask;
                break;
            default:
                ASSERT (npCharLen == 2);  // 唯一剩余的情况
                dwUTF32Char = btU8Char & c_btLead1Mask;
                break;
            }

            // 处理该字符的剩余字节
            for (INT_P i = 1; i < npCharLen; i++, psText++)
            {
                if (psText >= psTextEnd)
                {
                    blpFoundInvalidChar = TRUE;  // UTF8字符数据缺失
                    break;
                }

                btU8Char = (BYTE)*psText;

                if ((btU8Char & ~c_btContMask) != c_btCont)
                {
                    blpFoundInvalidChar = TRUE;  // 无效的UTF8字符
                    break;
                }

                dwUTF32Char <<= 6;
                dwUTF32Char |= (btU8Char & c_btContMask);
            }

            if (blpFoundInvalidChar)
                break;
        }

        //------------------------------------------------  转换为WCHAR字符

        if (dwUTF32Char <= 0xFFFF)
        {
            ASSERT (memBuf.IsInside (pwcResult, sizeof (WCHAR)));
            *pwcResult++ = (WCHAR)dwUTF32Char;
        }
        else
        {
            ASSERT (npCharLen > 1);  // 当字节数为1的时候,dwUTF32Char必定小于0xFFFF.

            dwUTF32Char -= 0x10000; // subtract value offset

            WCHAR wChar = (WCHAR)((dwUTF32Char >> 10) & 0x03FF);
            wChar += 0xD800;
            ASSERT (memBuf.IsInside (pwcResult, sizeof (WCHAR)));
            *pwcResult++ = wChar;

            wChar = (WCHAR)(dwUTF32Char & 0x03FF);
            wChar += 0xDC00;
            ASSERT (memBuf.IsInside (pwcResult, sizeof (WCHAR)));
            *pwcResult++ = wChar;
        }
    }

    ASSERT (memBuf.IsInside (pwcResult, sizeof (WCHAR)));
    *pwcResult = L'\0';  // 加入结束0字符

    //-------------------------------------------------

    // 记录是否找到了无效字符
    if (pblpFoundInvalidChar != NULL)
        *pblpFoundInvalidChar = blpFoundInvalidChar;

    // 返回转换后文本的长度
    if (pnpWStrLength != NULL)
        *pnpWStrLength = pwcResult - (WCHAR*)memBuf.GetPtr ();

    //!! 注意: 结果必须放入memBuf中,因为可能会对返回结果文本进行修改.
    if (blpCutBufSpace)
        return (WCHAR*)memBuf.Realloc ((const BYTE*)(pwcResult + 1) - memBuf.GetPtr ());  // 返回转换结果文本并释放多余空间
    else
        return (WCHAR*)memBuf.GetPtr (); */
}

U8CHAR* PrevU8Char (U8CHAR* psCurrent, const U8CHAR* psTextBegin)
{
    ASSERT_R_STR (psCurrent);
    ASSERT (psTextBegin != NULL);

    // 跳过前面的所有"10XX XXXX"格式字节
    for (INT_P npIndex = 0; npIndex < 6 && psCurrent > psTextBegin; npIndex++)
    {
        psCurrent--;

        if (((BYTE)*psCurrent & ~c_btContMask) != c_btCont)  // 不是"10XX XXXX"格式字节?
            return psCurrent;  // 返回该位置
    }

    return NULL;
}

U8CHAR* NextU8Char (U8CHAR* psCurrent)
{
    ASSERT_R_STR (psCurrent);

    // 跳过后面的所有"10XX XXXX"格式字节
    for (INT_P npIndex = 0; npIndex < 6 && *psCurrent != '\0'; npIndex++)
    {
        psCurrent++;

        if (((BYTE)*psCurrent & ~c_btContMask) != c_btCont)  // 不是"10XX XXXX"格式字节(顺便处理了可能提前出现的'\0'字符)?
            return psCurrent;  // 返回该位置
    }

    return NULL;
}

INT_P GetU8StrLength (const U8CHAR* psText)
{
    ASSERT_R_STR (psText);

    INT_P npLength = 0;

    while (*psText != '\0')
    {
        const INT_P npCharLen = GetUTF8CharBytes ((BYTE)*psText);
        if (npCharLen == -1)
            return -1;  // '\0'或者非法UTF8字符前缀

        psText++;

        for (INT_P i = 1; i < npCharLen; i++)
        {
            if (((BYTE)*psText & ~c_btContMask) != c_btCont)  // 无效的UTF8字符(顺便处理了可能提前出现的'\0'字符)
                return -1;

            psText++;
        }

        npLength++;
    }

    return npLength;
}

//-------------------------------------------------------------

const TCHAR* FindSubString (const TCHAR* psCurrent, const TCHAR* psEndMark, const TCHAR* szFindText, const BOOL_P blpIgnoreCase)
{
    ASSERT (psEndMark >= psCurrent);
    ASSERT_R_STR2 (psCurrent, psEndMark - psCurrent);
    ASSERT_R_STR (szFindText);

    if (IsEmptyStr (szFindText))
        return NULL;
    const INT_P npFindTextLength = _tcslen (szFindText);  // 获得被寻找文本的长度
    ASSERT (npFindTextLength > 0);

    while (psCurrent + npFindTextLength <= psEndMark)
    {
        // 进行文本比较
        INT_P npIndex = 0;
        while (TRUE)
        {
            if (blpIgnoreCase == FALSE)  // 不忽略大小写?
            {
                if (psCurrent [npIndex] != szFindText [npIndex])
                    break;
            }
            else
            {
                if (ToUpperCase (psCurrent [npIndex]) != ToUpperCase (szFindText [npIndex]))
                    break;
            }

            npIndex++;
            if (npIndex == npFindTextLength)
                return psCurrent;
        }

        psCurrent++;  // 到下一字符
    }

    return NULL;
}

const TCHAR* ReplaceSubString (const TCHAR* psFind, const TCHAR* psEndMark, const TCHAR* szNeedReplaceText,
        const TCHAR* szReplaceToText, const BOOL_P blpIgnoreCase, CVolString& strReplaceResult)
{
    ASSERT (psEndMark >= psFind);
    ASSERT_R_STR2 (psFind, psEndMark - psFind);
    ASSERT_R_STR (szNeedReplaceText);
    ASSERT_R_STR (szReplaceToText);

    do
    {
        if (IsEmptyStr (szNeedReplaceText) ||
                _tcscmp (szNeedReplaceText, szReplaceToText) == 0)
        {
            strReplaceResult.SetText (szNeedReplaceText);
            break;
        }

        strReplaceResult.Empty ();
        const INT_P npLen = _tcslen (szNeedReplaceText);

        while (TRUE)
        {
            // 寻找所指定的文本
            const TCHAR* ps = FindSubString (psFind, psEndMark, szNeedReplaceText, blpIgnoreCase);
            if (ps == NULL)  // 未找到?
            {
                strReplaceResult.AddText (psFind, psEndMark - psFind);
                break;
            }

            strReplaceResult.AddText (psFind, ps - psFind);
            strReplaceResult.AddText (szReplaceToText);

            psFind = ps + npLen;
        }
    }
    while (FALSE);

    return strReplaceResult.GetText ();
}

INT_P GetTextLengthWithoutTailSpaces (const TCHAR* psText, const TCHAR* psEndMark)
{
    ASSERT (psEndMark >= psText);
    ASSERT_R_STR2 (psText, psEndMark - psText);

    const TCHAR* ps = psEndMark - 1;
    while (ps >= psText)
    {
        if (IS_SPACE_CHAR_NOT_CHECK_ZERO (*ps) == FALSE)
            break;

        ps--;
    }

    return ps + 1 - psText;
}

const TCHAR* TextTrimAll (const TCHAR* psText, const TCHAR* psEndMark, INT_P* pnpLength)
{
    ASSERT (psEndMark >= psText);
    ASSERT_R_STR2 (psText, psEndMark - psText);
    ASSERT_RW_DATA_OR_NULL (pnpLength);

    psText = SkipSpaces (psText, psEndMark);
    if (pnpLength != NULL)
        *pnpLength = GetTextLengthWithoutTailSpaces (psText, psEndMark);

    return psText;
}

BOOL_P IsBoolValueText (const TCHAR* szValueText, BOOL_P* pblpValue)
{
    if (IsEmptyStr (szValueText) == FALSE)
    {
        // 清除首尾空白
        INT_P npValueTextLength = _tcslen (szValueText);
        const TCHAR* psValueText = TextTrimAll (szValueText, szValueText + npValueTextLength, &npValueTextLength);

        typedef struct
        {
            const TCHAR* m_szBoolStr;
            INT_P m_npBoolStrLen;
        }
        BOOL_STRING_INFO;
        static const BOOL_STRING_INFO cs_ainfBools [] =
        {
            {  _T_V_TRUE,     NUM_CHARS_OF_TEXT (_T_V_TRUE)     },
            {  _T_V_EN_TRUE,  NUM_CHARS_OF_TEXT (_T_V_EN_TRUE)  },
            {  _T ("1"),      NUM_CHARS_OF_TEXT (_T ("1"))      },

            {  _T (""),  0  },  // 用作切换到假

            {  _T_V_FALSE,     NUM_CHARS_OF_TEXT (_T_V_FALSE)     },
            {  _T_V_EN_FALSE,  NUM_CHARS_OF_TEXT (_T_V_EN_FALSE)  },
            {  _T ("0"),       NUM_CHARS_OF_TEXT (_T ("0"))       }
        };

        BOOL_P blpValue = TRUE;
        const BOOL_STRING_INFO* pInf = cs_ainfBools;
        for (INT_P npIndex = 0; npIndex < NUM_ELEMENTS_OF (cs_ainfBools); npIndex++, pInf++)
        {
            if (pInf->m_npBoolStrLen == 0)
            {
                ASSERT (IsEmptyStr (pInf->m_szBoolStr));
                blpValue = FALSE;
            }
            else if (npValueTextLength == pInf->m_npBoolStrLen &&
                    _tcsnicmp (psValueText, pInf->m_szBoolStr, npValueTextLength) == 0)
            {
                if (pblpValue != NULL)
                    *pblpValue = blpValue;
                return TRUE;
            }
        }
    }

    if (pblpValue != NULL)
        *pblpValue = FALSE;  // 默认设置为假
    return FALSE;  // 返回文本内容格式错误
}

//-------------------------------------------------------------

INT_P ClampInt (const INT_P npValue, const INT_P npMinimum, const INT_P npMaximum)
{
    ASSERT (npMaximum >= npMinimum);

    return (npValue < npMinimum ? npMinimum :
            (npValue > npMaximum ? npMaximum :
            npValue));
}

FLOAT ClampFloat (const FLOAT fValue, const FLOAT fMinimum, const FLOAT fMaximum)
{
    ASSERT (fMaximum >= fMinimum - NEAR_ZERO_FLOAT);

    return (fValue < fMinimum ? fMinimum :
            (fValue > fMaximum ? fMaximum :
            fValue));
}

FLOAT AmendRadian (FLOAT fRadian)
{
    fRadian = (FLOAT)fmod (fRadian, PI * 2.0f);

    if (fRadian < -PI)
        return fRadian + PI * 2.0f;
    else if (fRadian > PI)
        return fRadian - PI * 2.0f;
    else
        return fRadian;
}

INT_P LargestOrEqualPower2 (INT_P x)
{
    x--;
    x |= (x >> 1);
    x |= (x >> 2);
    x |= (x >> 4);
    x |= (x >> 8);
    x |= (x >> 16);
#ifdef _PF_64_BITS  // 为64位平台
    x |= (x >> 32);
#endif

    return x + 1;
}

FLOAT FloatCloseTo (FLOAT fCurrent, const FLOAT fDest, const FLOAT fAdjustValue)
{
    ASSERT (fAdjustValue > NEAR_ZERO_FLOAT);

    if (IsFloatEqual (fDest, fCurrent) == FALSE)
    {
        if (fDest > fCurrent)
        {
            fCurrent += fAdjustValue;
            if (fCurrent >= fDest)
                fCurrent = fDest;
        }
        else if (fDest < fCurrent)
        {
            fCurrent -= fAdjustValue;
            if (fCurrent <= fDest)
                fCurrent = fDest;
        }
    }

    return fCurrent;
}

static DOUBLE sProcessDouble (const DOUBLE db)
{
    DOUBLE dbInt;
    DOUBLE dbFrac = modf (db, &dbInt);
    if (dbFrac < 0)
        dbFrac = -dbFrac;

    return ((dbFrac >= 1.0 - NEAR_ZERO_DOUBLE) ? (dbInt + (dbInt < 0 ? -1 : 1)) : db);
}

INT_P FloorDouble (const DOUBLE dbValue)
{
    return (INT_P)floor (sProcessDouble (dbValue));
}

INT_P FixDouble (const DOUBLE dbValue)
{
    DOUBLE db;
    modf (sProcessDouble (dbValue), &db);
    return (INT_P)db;
}

DOUBLE RoundDouble (DOUBLE db, const INT_P npRound)
{
    if (IsDoubleEqualZero (db))
        return db;

    const BOOL_P blpNegative = (db < 0);
    if (blpNegative)
        db = -db;

    if (npRound < 0)
    {
        DOUBLE n = pow (10.0, (DOUBLE)-npRound);
        db /= n;
        if (modf (db + NEAR_ZERO_DOUBLE, &db) >= 0.5)
            db = db + 1;
        db *= n;
    }
    else if (npRound == 0)
    {
        if (modf (db + NEAR_ZERO_DOUBLE, &db) >= 0.5)
            db = db + 1;
    }
    else
    {
        DOUBLE n = pow (10.0, (DOUBLE)npRound);
        db *= n;
        if (modf (db + NEAR_ZERO_DOUBLE, &db) >= 0.5)
            db = db + 1;
        db /= n;
    }

    return (blpNegative ? -db : db);
}

//-------------------------------------------------------------

static BOOL_P s_blpSrand = FALSE;

void SetRandSeed (INT_P npSeed)
{
    if (npSeed == 0)
        npSeed = ::MGetTickCount ();

    s_blpSrand = TRUE;
    srand ((DWORD)npSeed);
}

DOUBLE randdouble ()
{
    if (s_blpSrand == FALSE)
    {
        s_blpSrand = TRUE;
        srand (::MGetTickCount ());
    }

    return (DOUBLE)rand () / (DOUBLE)RAND_MAX;
}

DOUBLE randdouble (const DOUBLE dbFrom, const DOUBLE dbTo)
{
    return dbFrom + (dbTo - dbFrom) * randdouble ();
}

INT_P randint ()
{
    if (s_blpSrand == FALSE)
    {
        s_blpSrand = TRUE;
        srand (::MGetTickCount ());
    }

    return rand ();
}

DWORD randdword ()
{
    // 因为randint所返回的最大值是32627,所以将两个随机数组合到一起.
    // 因为randint所返回的最大值是32627,所以所返回值必定小于INT_MAX.
    return ((((DWORD)randint () << 16) & 0xFFFF0000) | ((DWORD)randint () & 0x0000FFFF));
}

INT randint2 (INT lower, INT upper)
{
    if (upper < lower)
    {
        FAIL;
        SWAP_INT (upper, lower)
    }

    return ((INT)randdword () % (upper - lower + 1)) + lower;
}

INT_P randint (const INT_P upper)
{
    ASSERT (upper >= 0);
    return (randint () % (CLIP (upper, 0, INT_MAX - 1) + 1));
}

INT_P randint (INT_P lower, INT_P upper)
{
    if (upper < lower)
    {
        FAIL;
        SWAP_INT_P (upper, lower)
    }

    return (randint () % (MIN (INT_MAX - 1, upper - lower) + 1)) + lower;
}

DWORD GetBinHash (const BYTE* pData, const INT_P npDataSize)
{
    if (npDataSize <= 0)
        return 0;
    ASSERT_R_ADR (pData, npDataSize);

    const DWORD* pdw = (const DWORD*)pData;
    const INT_P npNumDWords = npDataSize / sizeof (DWORD);

    // 以DWORD为单位尺寸计算Hash
    DWORD dwHash = (DWORD)npDataSize;
    INT_P i;
    for (i = 0; i < npNumDWords; i++)
    {
        dwHash *= 5;  // 必须是质数
        dwHash += *pdw++;
    }

    // 以BYTE为单位尺寸计算剩余的Hash
    const BYTE* pb = (const BYTE*)pdw;
    const INT_P npNumBytes = npDataSize % sizeof (DWORD);
    for (i = 0; i < npNumBytes; i++)
    {
        dwHash *= 5;  // 必须是质数
        dwHash += *pb++;
    }
    ASSERT (pb == pData + npDataSize);

    return (dwHash & 0x7FFFFFFF);
}

//-------------------------------------------------------------

#if defined (_PF_WINDOWS)

BOOL_P GetInstancePath (CVolString& strPath)
{
    return GetInstancePath (NULL, strPath);
}

BOOL_P GetInstancePath (const HINSTANCE hInstance, CVolString& strPath)
#else
BOOL_P GetInstancePath (CVolString& strPath)
#endif
{
    strPath.Empty ();

#if defined (_PF_WINDOWS)
    TCHAR buf [MAX_PATH + 1];
    buf [0] = '\0';
    if (::GetModuleFileName (hInstance, buf, NUM_ELEMENTS_OF (buf) - 1) == 0)
        return FALSE;
#elif defined (_PF_LINUX)
    TCHAR buf [1024];
    INT_P npReadSize = readlink (_T ("/proc/self/exe"), buf, NUM_ELEMENTS_OF (buf) - 1);
    if (npReadSize < 0 || npReadSize > NUM_ELEMENTS_OF (buf) - 1)
    {
        TCHAR buf2 [256];
        _stprintf (buf2, "/proc/%d/exe", getpid ());
        npReadSize = readlink (buf2, buf, NUM_ELEMENTS_OF (buf) - 1);
        if (npReadSize < 0 || npReadSize > NUM_ELEMENTS_OF (buf) - 1)
            return FALSE;
    }
    buf [npReadSize] = '\0';
#endif

    TCHAR* pFnd = _tcsrchr (buf, OS_PATH_CHAR);
    if (pFnd != NULL)
        *(pFnd + 1) = '\0';

    strPath = buf;
    return TRUE;
}

BOOL_P IsAbsPath (const TCHAR* szOSPath)
{
    ASSERT_R_STR (szOSPath);

#if defined (_PF_WINDOWS)
    return (szOSPath [0] == OS_PATH_CHAR ||
            (szOSPath [0] != '\0' && szOSPath [1] == ':' && szOSPath [2] == OS_PATH_CHAR));
#else
    return (szOSPath [0] == OS_PATH_CHAR);
#endif
}

INT_P CounterChar (const TCHAR* psText, const INT_P npTextLength, const TCHAR chTest)
{
    ASSERT_R_STR2 (psText, npTextLength);
    ASSERT (chTest != '\0');

    INT_P npNumChars = 0;

    for (INT_P npIndex = 0; npIndex < npTextLength; npIndex++, psText++)
    {
        if (*psText == chTest)
            npNumChars++;
    }

    return npNumChars;
}

const TCHAR* AbsPathFileName2Rel (const TCHAR* szRootAbsPath, const TCHAR* szCheckAbsPathFileName, CVolString& strRelPathFileName)
{
    ASSERT_R_STR (szRootAbsPath);
    ASSERT_R_STR (szCheckAbsPathFileName);

    const TCHAR* ps;
    if (IsEmptyStr (szRootAbsPath) ||
            (ps = _tcsrchr (szCheckAbsPathFileName, OS_PATH_CHAR)) == NULL)
    {
        strRelPathFileName.SetText (szCheckAbsPathFileName);
    }
    else
    {
        ps++;

        AbsPath2Rel (szRootAbsPath, CVolString (szCheckAbsPathFileName, ps - szCheckAbsPathFileName).GetText (), strRelPathFileName);
        strRelPathFileName += ps;
    }

    return strRelPathFileName.GetText ();
}

const TCHAR* AbsPath2Rel (const TCHAR* szRootAbsPath, const TCHAR* szCheckAbsPath, CVolString& strRelPath)
{
    ASSERT_R_STR (szRootAbsPath);
    ASSERT_R_STR (szCheckAbsPath);

    // 检查是否均为非空绝对路径
    if (IsEmptyStr (szRootAbsPath) || IsAbsPath (szRootAbsPath) == FALSE ||
            IsEmptyStr (szCheckAbsPath) || IsAbsPath (szCheckAbsPath) == FALSE)
    {
        strRelPath.SetText (szCheckAbsPath);  // 无法转换,返回原路径.
        return strRelPath.GetText ();
    }

    // 确保根目录以路径符结尾
    CVolString strPath1;
    const TCHAR* psPath1;
    if (EndOf (szRootAbsPath, OS_PATH_CHAR) == FALSE)
    {
        strPath1.SetText (szRootAbsPath);
        strPath1.AddChar (OS_PATH_CHAR);
        psPath1 = strPath1.GetText ();
    }
    else
    {
        psPath1 = szRootAbsPath;
    }

    // 确保测试目录以路径符结尾
    CVolString strPath2 (szCheckAbsPath);
    if (strPath2.EndOf (OS_PATH_CHAR) == FALSE)
        strPath2.AddChar (OS_PATH_CHAR);
    const TCHAR* psPath2 = strPath2.GetText ();

    //-------------------------------------------------------------------------

    do
    {
        if (_tcsicmp (psPath1, psPath2) == 0)  // 两个目录完全相同?
        {
            // strRelPath.SetText (_T (".") OS_PATH_CHAR_TEXT);  // 返回当前路径符
            strRelPath.Empty ();  // 返回当前路径
            break;
        }

        // 两者不均为绝对路径?
        if (IsAbsPath (psPath1) == FALSE || IsAbsPath (psPath2) == FALSE)
        {
            strRelPath.SetText (szCheckAbsPath);  // 无法转换,返回原路径.
            break;
        }

    #ifdef _PF_WINDOWS
        ASSERT (psPath1 [0] != '\0' && psPath2 [0] != '\0');  // IsAbsPath中的算法决定

        if ((psPath1 [1] == ':') != (psPath2 [1] == ':') ||  // 携带驱动器符状态不一致?
                (psPath1 [1] == ':' && TO_UPPER_CASE (psPath1 [0]) != TO_UPPER_CASE (psPath2 [0])))  // 所处驱动器不一致?
        {
            strRelPath.SetText (szCheckAbsPath);  // 无法转换,返回原路径.
            break;
        }
    #endif

        //-------------------------------------------------------------------------

        do
        {
            const TCHAR* ps1 = _tcschr (psPath1, OS_PATH_CHAR);
            const TCHAR* ps2 = _tcschr (psPath2, OS_PATH_CHAR);
            ASSERT (ps1 != NULL && ps2 != NULL);  // 因为前面处理过,两者必定都以路径分隔符结束.

            const INT_P npLen = ps1 - psPath1;
            if (npLen != ps2 - psPath2 || _tcsnicmp (psPath1, psPath2, npLen) != 0)
                break;

            // 跳过路径分隔符
            psPath1 = ps1 + 1;
            psPath2 = ps2 + 1;
        }
        while (*psPath1 != '\0' && *psPath2 != '\0');

        //-------------------------------------------------------------------------

        strRelPath.Empty ();

        const INT_P npCount = CounterChar (psPath1, OS_PATH_CHAR);
        for (INT_P npIndex = 0; npIndex < npCount; npIndex++)
        {
            strRelPath.AddText (_T ("..") OS_PATH_CHAR_TEXT);
        }
        strRelPath += psPath2;
    }
    while (FALSE);

    return strRelPath.GetText ();
}

const TCHAR* LinkOSPath (const TCHAR* szPath1, const TCHAR* szPath2, CVolMem& memBuf, const TCHAR cPathChar)
{
    ASSERT_R_STR (szPath1);
    ASSERT_R_STR (szPath2);

    if (IsEmptyStr (szPath1))  // 路径1为空?
        return szPath2;  // 返回路径2

    if (IsEmptyStr (szPath2))  // 路径2为空?
        return szPath1;  // 返回路径1

    if (IsAbsPath (szPath2))  // 路径2为绝对目录?
        return szPath2;

    // 建立连接文本
    memBuf.Empty ();
    memBuf.AddOnlyText (szPath1);
    if (EndOf (szPath1, cPathChar) == FALSE)  // 不以路径符号结束?
        memBuf.AddChar (cPathChar);  // 附加一个路径符号
    memBuf.AddString (szPath2);  // 附带结束0字符

    //--------------------------------------------------  处理"."目录

    TCHAR bufFind [5];
    bufFind [0] = cPathChar;
    bufFind [1] = '.';
    bufFind [2] = cPathChar;
    bufFind [3] = '\0';

    const TCHAR* psBegin = memBuf.GetTextPtr ();
    while (TRUE)
    {
        const TCHAR* ps = _tcsstr (psBegin, bufFind);  // 寻找类似"/./"
        if (ps == NULL)  // 未找到?
            break;

        // 将"/."删除
        const INT_P npOffset = ps - memBuf.GetTextPtr ();
        memBuf.Remove (npOffset * sizeof (TCHAR), 2 * sizeof (TCHAR));
        psBegin = memBuf.GetTextPtr () + npOffset;
        ASSERT (npOffset >= 0 && npOffset < memBuf.GetSize () && *psBegin == cPathChar);  // 前面的算法决定
    }

    //--------------------------------------------------  处理".."目录

    bufFind [2] = '.';
    bufFind [3] = cPathChar;
    bufFind [4] = '\0';

    psBegin = memBuf.GetTextPtr ();
    const TCHAR* psFindBegin = psBegin;
    while (TRUE)
    {
        const TCHAR* ps = _tcsstr (psFindBegin, bufFind);  // 寻找类似"/../"
        if (ps == NULL)  // 未找到?
            break;

        const TCHAR* psEndChar = ps;  // 记录下此位置

        do
        {
            ps--;
            if (ps < psBegin)  // 回溯溢出?
                return szPath2;  // 返回路径2
        }
        while (*ps != cPathChar);
        ASSERT (*ps == cPathChar);  // 前面的算法决定

        // 删除相关部分
        const INT_P npOffset = ps - memBuf.GetTextPtr ();
        memBuf.Remove (npOffset * sizeof (TCHAR), (psEndChar - ps + 3) * sizeof (TCHAR));

        // 重新获取相关指针
        psBegin = memBuf.GetTextPtr ();
        psFindBegin = psBegin + npOffset;
        ASSERT (npOffset >= 0 && npOffset < memBuf.GetSize () && *psFindBegin == cPathChar);  // 前面的算法决定
    }

    // 返回处理结果路径
    return memBuf.GetTextPtr ();
}

BOOL_P MRemoveFile (const TCHAR* szFileName)
{
    ASSERT_R_STR (szFileName);

    if (IsEmptyStr (szFileName))
        return FALSE;

#if defined (_PF_WINDOWS)
    return ::DeleteFile (szFileName);
#elif defined (_PF_LINUX)
    return (::remove (szFileName) == 0);
#endif
}

BOOL_P CreateDirectoryTree (const TCHAR* szOSDirectoryName)
{
    ASSERT_R_STR (szOSDirectoryName);

    if (IsEmptyStr (szOSDirectoryName))
        return FALSE;

    // 去除掉目录尾部的路径符
    CVolString strBuf;
    szOSDirectoryName = RemoveEndPathChar (szOSDirectoryName, strBuf);

#if defined (_PF_WINDOWS)
    if (szOSDirectoryName [0] == '\0' ||  // 为空文本?
            (szOSDirectoryName [0] == '\\' && szOSDirectoryName [1] == '\0') ||  // 为"\"?
            (szOSDirectoryName [1] == ':' && szOSDirectoryName [2] == '\0') ||  // 为类似'c:"?
            (szOSDirectoryName [1] == ':' && szOSDirectoryName [2] == '\\' && szOSDirectoryName [3] == '\0') ||  // 为类似'c:\"?
            ::CreateDirectory (szOSDirectoryName, NULL))
    {
        return TRUE;
    }

    const DWORD dwError = ::GetLastError ();
    if (dwError == ERROR_ALREADY_EXISTS)  // 已经存在则返回真
        return TRUE;

    // 在Windows平台下自动创建中间目录
    if (dwError == ERROR_PATH_NOT_FOUND)  // 中间目录不存在?
    {
        const TCHAR* ps = _tcsrchr (szOSDirectoryName, OS_PATH_CHAR);  // 寻找上一级目录
        if (ps != NULL && ps [1] == '\0')  // 所找到的OS_PATH_CHAR位于目录结尾?
        {
            ps--;
            while (ps >= szOSDirectoryName && *ps != OS_PATH_CHAR)
                ps--;
            if (ps < szOSDirectoryName)
                ps = NULL;
        }

        if (ps != NULL)  // 找到了上一级目录?
        {
            CVolString str;
            str.SetText (szOSDirectoryName, ps - szOSDirectoryName);

            if (CreateDirectoryTree (str.GetText ()))  // 上一级目录创建成功?
                return ::CreateDirectory (szOSDirectoryName, NULL);
        }
    }

#elif defined (_PF_LINUX)

    if (mkdir (szOSDirectoryName, S_IFDIR | S_IREAD | S_IWRITE | S_IEXEC | S_IRGRP | S_IXGRP) == 0)
        return TRUE;

    if (errno == EEXIST)  // 已经存在则返回真
        return TRUE;

    if (errno == ENOENT)  // 中间目录不存在?
    {
        const TCHAR* ps = _tcsrchr (szOSDirectoryName, OS_PATH_CHAR);  // 寻找上一级目录
        if (ps != NULL && ps [1] == '\0')  // 所找到的OS_PATH_CHAR位于目录结尾?
        {
            ps--;
            while (ps >= szOSDirectoryName && *ps != OS_PATH_CHAR)
                ps--;
            if (ps < szOSDirectoryName)
                ps = NULL;
        }

        if (ps != NULL)  // 找到了上一级目录?
        {
            CVolString str;
            str.SetText (szOSDirectoryName, ps - szOSDirectoryName);

            if (CreateDirectoryTree (str.GetText ()))  // 上一级目录创建成功?
                return (mkdir (szOSDirectoryName, S_IFDIR | S_IREAD | S_IWRITE | S_IEXEC | S_IRGRP | S_IXGRP) == 0);
        }
    }

#endif

    return FALSE;
}

#ifdef _PF_WINDOWS

BOOL_P IsDotSubDirName (const TCHAR* szFileName)
{
    if (szFileName == NULL)
        return FALSE;
    ASSERT_R_STR (szFileName);

    return ((szFileName [0] == '.' && szFileName [1] == '\0') ||
            (szFileName [0] == '.' && szFileName [1] == '.' && szFileName [2] == '\0'));
}

static BOOL_P _RemoveDir (const TCHAR* szOSDirectoryName, const DIR_TREE_REMOVE_MODE enRemoveMode, const BOOL_P blpOnlyFailedWhileRemoveFile)
{
    ASSERT_R_STR (szOSDirectoryName);
    ASSERT (IsEmptyStr (szOSDirectoryName) == FALSE);

    WIN32_FIND_DATA infFindFile;

    CVolString strDir (szOSDirectoryName);
    strDir.AddChar (OS_PATH_CHAR);

    const HANDLE hFind = FindFirstFile ((strDir + _T ("*.*")).GetText (), &infFindFile);
    if (hFind != INVALID_HANDLE_VALUE)
    {
        const DIR_TREE_REMOVE_MODE enChildRemoveMode = (
                enRemoveMode == DTRM_CLEAN_CONTENT ? DTRM_REMOVE_ALL : enRemoveMode);

        do
        {
            if (IsDotSubDirName (infFindFile.cFileName) == FALSE)  // 不为"."或".."?
            {
                if ((infFindFile.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) != 0)
                {
                    // 如果是目录,则进入递归调用.
                    if (_RemoveDir ((strDir + infFindFile.cFileName).GetText (), enChildRemoveMode, blpOnlyFailedWhileRemoveFile) == FALSE)
                    {
                        FindClose (hFind);
                        return FALSE;
                    }
                }
                else
                {
                    if (::DeleteFile ((strDir + infFindFile.cFileName).GetText ()) == FALSE)  // 如果是文件则直接删除
                    {
                        FindClose (hFind);
                        return FALSE;
                    }
                }
            }
        }
        while (FindNextFile (hFind, &infFindFile));

        FindClose (hFind);
    }

    if (enRemoveMode != DTRM_REMOVE_ALL)  // 不为删除所有内容?
        return TRUE;

    if (blpOnlyFailedWhileRemoveFile)  // 仅当删除文件失败时才会出错返回?
    {
        ::RemoveDirectory (szOSDirectoryName);
        return TRUE;
    }

#ifdef _DEBUG
    const BOOL_P blpRemoveSucceeded = ::RemoveDirectory (szOSDirectoryName);
    if (blpRemoveSucceeded == FALSE)
        TRACE_WIN_LAST_ERROR
    return blpRemoveSucceeded;
#else
    return ::RemoveDirectory (szOSDirectoryName);
#endif
}

BOOL_P RemoveDirectoryTree (const TCHAR* szOSDirectoryName, const DIR_TREE_REMOVE_MODE enRemoveMode, const BOOL_P blpOnlyFailedWhileRemoveFile)
{
    ASSERT_R_STR (szOSDirectoryName);

    // 去除掉目录尾部的路径符
    CVolString strBuf;
    szOSDirectoryName = RemoveEndPathChar (szOSDirectoryName, strBuf);

    // 避免删除根目录
    if (IsEmptyStr (szOSDirectoryName)
        #ifdef _PF_WINDOWS
            || (szOSDirectoryName [1] == ':' && szOSDirectoryName [2] != '\0' && szOSDirectoryName [3] == '\0')
        #endif
            )
    {
        return FALSE;
    }

    if (IsOSFileExist (szOSDirectoryName) == FALSE)  // 该目录不存在?
        return TRUE;

    return _RemoveDir (szOSDirectoryName, enRemoveMode, blpOnlyFailedWhileRemoveFile);
}

BOOL_P IsFileSizeAndTimeSame (const TCHAR* szFileName1, const TCHAR* szFileName2)
{
    WIN32_FILE_ATTRIBUTE_DATA inf1;
    WIN32_FILE_ATTRIBUTE_DATA inf2;

    return (GetFileAttributesEx (szFileName1, GetFileExInfoStandard, &inf1) &&
            GetFileAttributesEx (szFileName2, GetFileExInfoStandard, &inf2) &&
            inf1.ftLastWriteTime.dwLowDateTime == inf2.ftLastWriteTime.dwLowDateTime &&
            inf1.ftLastWriteTime.dwHighDateTime == inf2.ftLastWriteTime.dwHighDateTime &&
            inf1.nFileSizeLow == inf2.nFileSizeLow &&
            inf1.nFileSizeHigh == inf2.nFileSizeHigh);
}

BOOL_P MCopyFile (const TCHAR* szSourceFileName, const TCHAR* szDestFileName, const FILE_COPY_OVERRIDE_MODE enOverrideMode)
{
    if (IsEmptyStr (szSourceFileName) ||
            IsEmptyStr (szDestFileName))
    {
        return FALSE;
    }

    BOOL blFailIfExists;
    switch (enOverrideMode)
    {
    case FCOM_IGNORE:
        if (::IsOSFileExist (szDestFileName))
            return TRUE;
    case FCOM_FAIL:
        blFailIfExists = TRUE;
        break;

    case FCOM_FAST:
        if (IsFileSizeAndTimeSame (szSourceFileName, szDestFileName))
            return TRUE;
    default:
        ASSERT (enOverrideMode == FCOM_OVERRIDE || enOverrideMode == FCOM_FAST);
        blFailIfExists = FALSE;
        break;
    }

    if (_tcsicmp (szSourceFileName, szDestFileName) == 0)
    {
        if (::IsOSFileExist (szSourceFileName) == FALSE)
        {
            SetLastError (ERROR_FILE_NOT_FOUND);
            return FALSE;
        }

        return TRUE;
    }

    return ::CopyFile (szSourceFileName, szDestFileName, blFailIfExists);
}

BOOL_P MCopyFileAutoCreateDir (const TCHAR* szSourceFileName, const TCHAR* szDestFileName, const FILE_COPY_OVERRIDE_MODE enOverrideMode)
{
    ASSERT_R_STR (szSourceFileName);
    ASSERT_R_STR (szDestFileName);

    if (::MCopyFile (szSourceFileName, szDestFileName, enOverrideMode))  // 复制成功?
        return TRUE;

    if (::GetLastError () == ERROR_PATH_NOT_FOUND)  // 中间目录不存在?
    {
        CVolString strPath;
        if (CreateDirectoryTree (::GetOSFilePathPart (szDestFileName, strPath)) == FALSE)  // 创建中间目录失败?
            return FALSE;

        return ::MCopyFile (szSourceFileName, szDestFileName, enOverrideMode);
    }

    return FALSE;
}

const TCHAR* RemoveEndPathChar (const TCHAR* szPath, CVolString& strBuf)
{
    ASSERT_R_STR (szPath);

    if (IsEmptyStr (szPath) || szPath [1] == '\0')  // 为空或者只有1个字符?
        return szPath;

    const INT_P npLength = _tcslen (szPath);
    ASSERT (npLength >= 2);  // 前面检查过
    while (szPath [npLength - 1] == OS_PATH_CHAR)  // 以路径字符结束?
    {
    #if defined (_PF_WINDOWS)
        if (szPath [npLength - 2] == ':')  // 避免删除驱动器符后的路径字符
            break;
    #endif

        strBuf.SetText (szPath, npLength - 1);
        return strBuf.GetText ();
    }

    return szPath;
}

// 返回指定目录/文件是否存在
BOOL_P IsOSFileExist (const TCHAR* szFileName)
{
    ASSERT_R_STR (szFileName);

    if (IsEmptyStr (szFileName))
        return FALSE;

    CVolString strBuf;
#if defined (_PF_WINDOWS)
    return (GetFileAttributes (RemoveEndPathChar (szFileName, strBuf)) != INVALID_FILE_ATTRIBUTES);
#elif defined (_PF_LINUX)
    return (access (RemoveEndPathChar (szFileName, strBuf), F_OK) == 0);
#endif
}

// 返回指定目录是否存在
BOOL_P IsOSDirExist (const TCHAR* szDir)
{
    ASSERT_R_STR (szDir);

    if (IsEmptyStr (szDir))
        return FALSE;

    CVolString strBuf;
    const DWORD dwAttr = GetFileAttributes (RemoveEndPathChar (szDir, strBuf));
    return (dwAttr != INVALID_FILE_ATTRIBUTES && (dwAttr & FILE_ATTRIBUTE_DIRECTORY) != 0);
}

static BOOL_P sCopyFiles (const CVolString& strSrcOSDir, const CVolString& strDestOSDir, const TCHAR* szMatchFiles,
        const FILE_COPY_OVERRIDE_MODE enFileCopyOverrideMode, const BOOL_P blpRecursiveSubDir, CMStringArray* psaryCopyFailFileNames)
{
    // 本函数的进入前提
    ASSERT_R_STR (szMatchFiles);
    ASSERT (strSrcOSDir.IsEmpty () == FALSE &&  strSrcOSDir.EndOf (OS_PATH_CHAR) &&
            strDestOSDir.IsEmpty () == FALSE && strDestOSDir.EndOf (OS_PATH_CHAR) &&
            IsEmptyStr (szMatchFiles) == FALSE);
    ASSERT_RW_DATA_OR_NULL (psaryCopyFailFileNames);

    WIN32_FIND_DATA infFindFile;
    const HANDLE hFind = FindFirstFile ((strSrcOSDir + szMatchFiles).GetText (), &infFindFile);

    BOOL_P blpSucceeded = TRUE;
    if (hFind != INVALID_HANDLE_VALUE)
    {
        do
        {
            if (IsDotSubDirName (infFindFile.cFileName) == FALSE)  // 不为"."或".."?
            {
                if ((infFindFile.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) == 0)  // 不为子目录?
                {
                    CVolString strSourceFileName (strSrcOSDir + infFindFile.cFileName);
                    CVolString strDestFileName (strDestOSDir + infFindFile.cFileName);

                    if (::MCopyFile (strSourceFileName.GetText (), strDestFileName.GetText (), enFileCopyOverrideMode) == FALSE)
                    {
                        if (psaryCopyFailFileNames != NULL)
                        {
                            // 记录下所复制的源和目的文件名
                            psaryCopyFailFileNames->Add (strSourceFileName.GetText ());
                            psaryCopyFailFileNames->Add (strDestFileName.GetText ());
                        }

                        blpSucceeded = FALSE;
                    }
                }
                else if (blpRecursiveSubDir)  // 递归进入子目录?
                {
                    // 创建该子目录
                    CVolString strNewDir (strDestOSDir + infFindFile.cFileName);
                    ::CreateDirectory (strNewDir.GetText (), NULL);
                    strNewDir.AddChar (OS_PATH_CHAR);

                    CVolString str (strSrcOSDir + infFindFile.cFileName + OS_PATH_CHAR_TEXT);
                    if (sCopyFiles (str, strNewDir, szMatchFiles, enFileCopyOverrideMode,
                            blpRecursiveSubDir, psaryCopyFailFileNames) == FALSE)
                    {
                        blpSucceeded = FALSE;
                    }
                }
            }
        }
        while (FindNextFile (hFind, &infFindFile));

        FindClose (hFind);
    }

    return blpSucceeded;
}

BOOL_P MCopyFiles (const TCHAR* szSrcOSDir, const TCHAR* szDestOSDir, const TCHAR* szMatchFiles,
        const FILE_COPY_OVERRIDE_MODE enFileCopyOverrideMode, const BOOL_P blpRecursiveSubDir,
        CMStringArray* psaryCopyFailFileNames)
{
    ASSERT_R_STR (szSrcOSDir);
    ASSERT_R_STR (szDestOSDir);
    ASSERT_R_STR (szMatchFiles);
    ASSERT_RW_DATA_OR_NULL (psaryCopyFailFileNames);

    if (psaryCopyFailFileNames != NULL)
        psaryCopyFailFileNames->RemoveAll ();

    if (IsOSFileExist (szSrcOSDir) == FALSE ||  // 源目录不存在?
            IsOSFileExist (szDestOSDir) == FALSE)  // 目的目录不存在?
    {
        return FALSE;
    }

    CVolString strSrcOSDir (szSrcOSDir);
    strSrcOSDir.CheckAddPathChar ();

    CVolString strDestOSDir (szDestOSDir);
    strDestOSDir.CheckAddPathChar ();

    if (IsEmptyStr (szMatchFiles))
        szMatchFiles = _T ("*.*");

    return sCopyFiles (strSrcOSDir, strDestOSDir, szMatchFiles, enFileCopyOverrideMode, blpRecursiveSubDir, psaryCopyFailFileNames);
}

static void sSetClassesRegisterKey (const TCHAR* szKeyName, const TCHAR* szKeyValue)
{
    ASSERT_R_STR (szKeyName);
    ASSERT_R_STR (szKeyValue);
    ASSERT (IsEmptyStr (szKeyName) == FALSE &&
            IsEmptyStr (szKeyValue) == FALSE);

    const INT_P npDataSize = (_tcslen (szKeyValue) + 1) * sizeof (TCHAR);

    HKEY hKey;
    if (::RegCreateKeyEx (HKEY_CLASSES_ROOT, szKeyName, 0, REG_NONE,
            REG_OPTION_NON_VOLATILE, KEY_WRITE, NULL, &hKey, NULL) == ERROR_SUCCESS)
    {
        RegSetValueEx (hKey, _T (""), NULL, REG_SZ, (const BYTE *)szKeyValue, (DWORD)npDataSize);
        RegCloseKey (hKey);
    }

    if (::RegCreateKeyEx (HKEY_CURRENT_USER, (CVolString (_T ("Software\\Classes\\")) + szKeyName).GetText (),
            0, REG_NONE, REG_OPTION_NON_VOLATILE, KEY_WRITE, NULL, &hKey, NULL) == ERROR_SUCCESS)
    {
        RegSetValueEx (hKey, _T (""), NULL, REG_SZ, (const BYTE *)szKeyValue, (DWORD)npDataSize);
        RegCloseKey (hKey);
    }
}

void RegisterFileRelation (const TCHAR* szExeFileName, const TCHAR* szExtName, const TCHAR* szExtKeyName,
        const TCHAR* szModuleFileName, const INT_P npIconIndex, const TCHAR* szDescribe)
{
    ASSERT_R_STR (szExeFileName);
    ASSERT_R_STR (szExtName);
    ASSERT_R_STR (szExtKeyName);
    ASSERT_R_STR (szModuleFileName);
    ASSERT_R_STR (szDescribe);

    if (IsEmptyStr (szExtName) ||
            IsEmptyStr (szExtKeyName) ||
            npIconIndex == -1)  // -1在ExtraIcon中为取图标数目
    {
        return;
    }

    TCHAR acExePath [MAX_PATH];
    if (IsEmptyStr (szExeFileName) || IsEmptyStr (szModuleFileName))
    {
        acExePath [0] = '\0';
        if (::GetModuleFileName (NULL, acExePath, NUM_ELEMENTS_OF (acExePath) - 1) <= 0)
            return;

        if (IsEmptyStr (szExeFileName))
            szExeFileName = acExePath;

        if (IsEmptyStr (szModuleFileName))
            szModuleFileName = acExePath;
    }

    CVolString strExtKeyName (szExtKeyName);
    CVolString strIconValue;
    strIconValue.Format (_T ("%s,%d"), szModuleFileName, (INT)npIconIndex);  // 使用负值表示图标ID

    sSetClassesRegisterKey (szExtName, szExtKeyName);
    sSetClassesRegisterKey (szExtKeyName, szDescribe);
    sSetClassesRegisterKey ((strExtKeyName + _T ("\\DefaultIcon")).GetText (), strIconValue.GetText ());
    // sSetClassesRegisterKey (strExtKeyName + _T ("\\Shell"), _T ("Open"));
    sSetClassesRegisterKey ((strExtKeyName + _T ("\\Shell\\Open\\Command")).GetText (),
            (CVolString (szExeFileName) + _T (" \"%1\"")).GetText ());
}

BOOL_P GetFileInfo (const TCHAR* szFileName, WIN32_FIND_DATA* pinfFile)
{
    ASSERT_R_STR (szFileName);
    ASSERT_RW_DATA (pinfFile);

    ZERO_MEM (pinfFile, sizeof (WIN32_FIND_DATA));

    if (IsEmptyStr (szFileName))
        return FALSE;

    const HANDLE hFile = ::FindFirstFile (szFileName, pinfFile);
    if (hFile == INVALID_HANDLE_VALUE)
        return FALSE;
    ::FindClose (hFile);

    return TRUE;
}

INT_P FindAllMatchFiles (const TCHAR* szFindDir, const TCHAR* szMatchFileName,
        const BOOL_P blpFindSubDirName, CMStringArray& saryFoundFileNames, const BOOL_P blpAddDir)
{
    ASSERT_R_STR (szFindDir);
    ASSERT_R_STR (szMatchFileName);
    ASSERT (IsEmptyStr (szMatchFileName) == FALSE);

    saryFoundFileNames.RemoveAll ();

    if (IsEmptyStr (szFindDir))
        return 0;

    // 寻找需要匹配的后缀名称
    const TCHAR* psMatchExtName = _tcschr (szMatchFileName, '.');
    if (psMatchExtName != NULL)
    {
        if (psMatchExtName [1] == '\0' ||  // 未指定后缀?
                _tcschr (psMatchExtName, '*') != NULL ||
                _tcschr (psMatchExtName, '?') != NULL)  // 中间包含有通配符?
        {
            psMatchExtName = NULL;  // 设置为无需要匹配的后缀名称
        }
    }

    CVolString strFindDir (szFindDir);
    strFindDir.CheckAddPathChar ();  // 加上路径符

    WIN32_FIND_DATA infFindFile;
    const HANDLE hFind = FindFirstFile ((strFindDir + szMatchFileName).GetText (), &infFindFile);

    if (hFind != INVALID_HANDLE_VALUE)
    {
        do
        {
            if (IsDotSubDirName (infFindFile.cFileName) == FALSE &&  // 不为"."或".."?
                    // 避免寻找"*.txt"却找到了类似"*.txt-"
                    (psMatchExtName == NULL || IEndOf (infFindFile.cFileName, psMatchExtName)))
            {
                if (blpFindSubDirName == ((infFindFile.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) != 0))  // 文件类型匹配?
                {
                    if (blpAddDir)  // 需要加入目录名?
                        saryFoundFileNames.Add ((strFindDir + infFindFile.cFileName).GetText ());
                    else
                        saryFoundFileNames.Add (infFindFile.cFileName);
                }
            }
        }
        while (FindNextFile (hFind, &infFindFile));

        FindClose (hFind);
    }

    return saryFoundFileNames.GetCount ();
}

void ActiveOtherAppWindow (HWND hWnd)
{
    ASSERT (hWnd != NULL);

    DWORD dwThreadId1 = GetWindowThreadProcessId (hWnd, NULL);
    DWORD dwThreadId2 = GetCurrentThreadId ();

    AttachThreadInput (dwThreadId2, dwThreadId1, TRUE);
    ::SetActiveWindow (hWnd);
    ::SetForegroundWindow (hWnd);
    AttachThreadInput (dwThreadId2, dwThreadId1, FALSE);
}

BOOL_P SetClipboardText (const TCHAR* szClipText)
{
    ASSERT_R_STR (szClipText);

    if (::OpenClipboard (NULL) == FALSE)
        return FALSE;

    ::EmptyClipboard ();

    const INT_P npLen = _tcslen (szClipText);
    if (npLen > 0)
    {
        INT_P npSize = (npLen + 1) * sizeof (TCHAR);
        HGLOBAL hMem = ::GlobalAlloc (GMEM_MOVEABLE, (SIZE_T)npSize);
        if (hMem != NULL)
        {
            COPY_MEM (GlobalLock (hMem), szClipText, npSize);
            GlobalUnlock (hMem);

        #ifdef _UNICODE
            ::SetClipboardData (CF_UNICODETEXT, hMem);
        #else
            ::SetClipboardData (CF_TEXT, hMem);
        #endif
        }

    #ifdef _UNICODE
        CVolMem memBuf;
        const CHAR* ps = GetMbsText (szClipText, memBuf, NULL);
        npSize = (strlen (ps) + 1) * sizeof (CHAR);

        hMem = ::GlobalAlloc (GMEM_MOVEABLE, (SIZE_T)npSize);
        if (hMem != NULL)
        {
            COPY_MEM (GlobalLock (hMem), ps, npSize);
            GlobalUnlock (hMem);

            ::SetClipboardData (CF_TEXT, hMem);
        }
    #endif
    }

    ::CloseClipboard ();
    return TRUE;
}

const TCHAR* GetCurrentClipboardText (CVolMem& memBuf)
{
    if (::OpenClipboard (NULL) == FALSE)
        return _T ("");

    const TCHAR* szClipText = _T ("");

    do
    {
        HGLOBAL hData;

    #ifdef _UNICODE
        hData = ::GetClipboardData (CF_UNICODETEXT);
        if (hData != NULL)
        {
            memBuf.Append (::GlobalLock (hData), ::GlobalSize (hData));
            memBuf.AddDWord (0);  // 加入'\0'字符. 为了避免前面的文本不以2字节为单位,此处加4个字节的0.
            szClipText = memBuf.GetTextPtr ();

            ::GlobalUnlock (hData);
            break;
        }
    #endif

        hData = ::GetClipboardData (CF_TEXT);
        if (hData != NULL)
        {
        #ifdef _UNICODE
            CVolMem memBuf2;
            memBuf2.Append (::GlobalLock (hData), ::GlobalSize (hData));
            memBuf2.AddDWord (0);
            szClipText = GetWideText ((const CHAR*)memBuf2.GetPtr (), memBuf, NULL);
        #else
            memBuf.CopyFrom (::GlobalLock (hData), ::GlobalSize (hData));
            memBuf.AddDWord (0);
            szClipText = (const CHAR*)memBuf.GetPtr ();
        #endif

            ::GlobalUnlock (hData);
        }
    }
    while (FALSE);

    ::CloseClipboard ();
    return szClipText;
}

// psRetData指向具有MAX_PATH个字符空间的缓冲区
static BOOL_P sGetRegKey (const HKEY hKey, const TCHAR* szSubKey, TCHAR* psRetData)
{
    ASSERT_R_STR (szSubKey);
    ASSERT_RW_ADR (psRetData, MAX_PATH * sizeof (TCHAR));

    *psRetData = '\0';

    HKEY hKeyOpened;
    if (RegOpenKeyEx (hKey, szSubKey, 0, KEY_QUERY_VALUE, &hKeyOpened) != ERROR_SUCCESS)
        return FALSE;

    LONG lDataSize = MAX_PATH * sizeof (TCHAR);
    const BOOL_P blpSucceeded = (RegQueryValue (hKeyOpened, NULL, psRetData, &lDataSize) == ERROR_SUCCESS);
    RegCloseKey (hKeyOpened);

    return blpSucceeded;
}

void ShellOpenFileInsideFolder (const TCHAR* szFileName)
{
    ASSERT_R_STR (szFileName);

    ShellExecute (NULL, _T ("open"), _T ("explorer.exe"),
            (_T (" /select, \"") + CVolString (szFileName) + _T ("\"")).GetText (),
            NULL, SW_SHOWNORMAL);
}

DOUBLE GetSystemUIScale ()
{
    MONITORINFOEX miex;
    miex.cbSize = sizeof(miex);
    GetMonitorInfo (MonitorFromWindow (GetDesktopWindow (), MONITOR_DEFAULTTONEAREST), &miex);

    DEVMODE dm;
    dm.dmSize = sizeof(dm);
    dm.dmDriverExtra = 0;
    EnumDisplaySettings (miex.szDevice, ENUM_CURRENT_SETTINGS, &dm);

    // 计算并返回缩放比例(横纵向缩放比例是一致的)
    return ((DOUBLE)dm.dmPelsWidth / (DOUBLE)(miex.rcMonitor.right - miex.rcMonitor.left));
}

DOUBLE GetMoniterDPI (HWND hWnd)
{
    if (hWnd == NULL)
        hWnd = GetDesktopWindow ();

    INT nDPI = 0;

    const HINSTANCE hInstWinSta = LoadLibrary (_T ("SHCore.dll"));
    if (hInstWinSta != NULL)
    {
        typedef HRESULT (WINAPI *PFN_GDFM) (HMONITOR, INT, UINT*, UINT*);
        PFN_GDFM fnGetDpiForMonitor = (PFN_GDFM)GetProcAddress (hInstWinSta, "GetDpiForMonitor");
        if (fnGetDpiForMonitor != NULL)
        {
            UINT dpiX;
            fnGetDpiForMonitor (MonitorFromWindow (hWnd, MONITOR_DEFAULTTONEAREST), 0, &dpiX, (UINT*)&nDPI);
        }

        FreeLibrary (hInstWinSta);
    }

    if (nDPI == 0)
    {
	    const HDC hDC = ::GetDC (hWnd);
        nDPI = GetDeviceCaps (hDC, LOGPIXELSY);
        ::ReleaseDC (hWnd, hDC);
    }
    
    const DOUBLE dbDpi = (DOUBLE)nDPI / 96.0;
    return MAX (1.0, dbDpi);
}

void MSetProcessDpiAwareness (INT nMode)
{
    const HINSTANCE hInstWinSta = LoadLibrary (_T ("SHCore.dll"));
    if (hInstWinSta != NULL)
    {
        typedef HRESULT (WINAPI *FN_SET_PROCESS_DPI_AWARENESS)(INT nValue);

        FN_SET_PROCESS_DPI_AWARENESS fnSetProcessDpiAwareness = (FN_SET_PROCESS_DPI_AWARENESS)GetProcAddress (hInstWinSta, "SetProcessDpiAwareness");
        if (fnSetProcessDpiAwareness != NULL)
            fnSetProcessDpiAwareness (nMode);

        FreeLibrary (hInstWinSta);
    }
}

BOOL_P OpenURL (const TCHAR* szURL, const INT_P npShowWindow)
{
    ASSERT_R_STR (szURL);

    // 处理在文件管理器中定位文件
    if (_tcsnicmp (szURL, _T_BROWSE_ITEM_HREF_LEADER, NUM_CHARS_OF_TEXT (_T_BROWSE_ITEM_HREF_LEADER)) == 0)
    {
        ShellOpenFileInsideFolder (szURL + NUM_CHARS_OF_TEXT (_T_BROWSE_ITEM_HREF_LEADER));
        return TRUE;
    }

    if ((INT_P)ShellExecute (NULL, _T ("open"), szURL, NULL, NULL,
            (INT)(npShowWindow < 0 ? SW_SHOWDEFAULT : npShowWindow)) > HINSTANCE_ERROR)
    {
        return TRUE;
    }

    TCHAR acKeyBuf [MAX_PATH + 1];
    acKeyBuf [0] = '\0';

    if (sGetRegKey (HKEY_CLASSES_ROOT, _T (".htm"), acKeyBuf) == FALSE)
        return FALSE;

    _tcscat (acKeyBuf, _T("\\shell\\open\\command"));
    if (sGetRegKey (HKEY_CLASSES_ROOT, acKeyBuf, acKeyBuf) == FALSE)
        return FALSE;

    TCHAR* ps = _tcsstr (acKeyBuf, _T("\"%1\""));
    if (ps != NULL)
    {
        *ps = '\0';
    }
    else
    {
        ps = _tcsstr (acKeyBuf, _T ("%1"));

        if (ps != NULL)
            *ps = '\0';
        else
            ps = acKeyBuf + _tcslen (acKeyBuf) - 1;
    }

    CVolString str (ps);
    str.AddChar (' ');
    str.AddText (szURL);
    return RunCommandLine (str.GetText (), FALSE, npShowWindow);
}

void GlobalUnlockAndFree (const HGLOBAL hGlobal)
{
	if (hGlobal == NULL)
		return;

	ASSERT (GlobalFlags (hGlobal) != GMEM_INVALID_HANDLE);
	UINT nCount = (GlobalFlags (hGlobal) & GMEM_LOCKCOUNT);
	while (nCount--)
		GlobalUnlock (hGlobal);

	GlobalFree (hGlobal);
}

#endif

const TCHAR* GetAbsOSPathOfFileName (const TCHAR* szFileName, CVolString& strPath)
{
    ASSERT_R_STR (szFileName);

    strPath.Empty ();

    if (IsAbsPath (szFileName))
    {
        const TCHAR* ps = _tcsrchr (szFileName, OS_PATH_CHAR);

        if (ps != NULL)
        {
            // 检查该路径字符是否为路径的一部分
            if (ps > szFileName  // 不位于路径的首部?
                #if defined (_PF_WINDOWS)
                    && *(ps - 1) != ':'  // 前面不为盘符?
                #endif
                )
            {
                ps--;  // 该路径字符是多余的
            }

            strPath.SetText (szFileName, ps + 1 - szFileName);
        }
    }

    return strPath.GetText ();
}

const TCHAR* GetOSFilePathPart (const TCHAR* szFileName, CVolString& strPath)
{
    ASSERT_R_STR (szFileName);

    if (IsEmptyStr (szFileName))
    {
        strPath.Empty ();
    }
    else
    {
        const TCHAR* ps = _tcsrchr (szFileName, OS_PATH_CHAR);

        if (ps != NULL)
            strPath.SetText (szFileName, ps + 1 - szFileName);  // 返回文本包括OS_PATH_CHAR符号
        else
            strPath.Empty ();
    }

    return strPath.GetText ();
}

const TCHAR* GetOSFileNameWithoutPath (const TCHAR* szFileName)
{
    ASSERT_R_STR (szFileName);

    const TCHAR* ps = _tcsrchr ((TCHAR*)szFileName, OS_PATH_CHAR);

    if (ps != NULL)
        return ps + 1;
    else
        return szFileName;
}

const TCHAR* GetOSFilePureName (const TCHAR* szFileName, CVolString& strBuf)
{
    ASSERT_R_STR (szFileName);

    const TCHAR* ps = GetOSFileNameWithoutPath (szFileName);

    const TCHAR* psExt = _tcschr (ps, '.');  // 由于有类似".9.png"这样的后缀,所以此处只能正向查找(前提是路径部分已经被去除).
    if (psExt == NULL)
        return ps;

    strBuf.SetText (ps, psExt - ps);
    return strBuf.GetText ();
}

CVolString ChangeFileNameExt (const TCHAR* szFileName, const TCHAR* szNewExt)
{
    ASSERT_R_STR (szFileName);
    ASSERT_R_STR (szNewExt);
    ASSERT (szNewExt [0] != '.');

    CVolString strNewFileName;

    const TCHAR* psExt = FindFileNameExtDotChar (szFileName);
    if (psExt != NULL)
    {
        strNewFileName.SetText (szFileName, psExt + 1 - szFileName);
    }
    else
    {
        strNewFileName.SetText (szFileName);
        strNewFileName.AddChar ('.');
    }
    strNewFileName += szNewExt;

    return strNewFileName;
}

const TCHAR* GetFileExtName (const TCHAR* szFileName)
{
    ASSERT_R_STR (szFileName);

    const TCHAR* psExt = FindFileNameExtDotChar (szFileName);

    if (psExt != NULL)
        return psExt + 1;  // 跳过'.'字符
    else
        return _T ("");
}

BOOL_P MGetCurrentDirectory (TCHAR* psBuf, const INT_P npBufLength)
{
    ASSERT (npBufLength > 0);
    ASSERT_RW_ADR (psBuf, npBufLength * sizeof (TCHAR));

#if defined (_PF_WINDOWS)
    return (GetCurrentDirectory ((DWORD)npBufLength, psBuf) > 0);
#else
    const TCHAR* ps = getcwd (psBuf, npBufLength);
    if (ps == NULL)
        return FALSE;
    //   On success, these functions return a pointer to a string containing the
    // pathname  of  the  current working directory.  In the case getcwd() and
    // getwd() this is the same value as buf.
    ASSERT (ps == psBuf);
    return TRUE;
#endif
}

BOOL_P MSetCurrentDirectory (const TCHAR* szNewDir)
{
    ASSERT_R_STR (szNewDir);

    if (IsEmptyStr (szNewDir))
        return FALSE;

#if defined (_PF_WINDOWS)
    return SetCurrentDirectory (szNewDir);
#else
    return (chdir (szNewDir) == 0);
#endif
}

//-------------------------------------------------------------

H_LIB MLoadLibrary (const TCHAR* szLibraryName)
{
    ASSERT_R_STR (szLibraryName);

    if (IsEmptyStr (szLibraryName))
        return 0;

    // 获取库文件名的路径部分
    CVolString strPath;
    const TCHAR* szPath = GetAbsOSPathOfFileName (szLibraryName, strPath);

    TCHAR acOldPath [MAX_PATH];
    BOOL_P blpDirChanged;
    if (IsEmptyStr (szPath) == FALSE &&  // 库文件路径获取成功?
            MGetCurrentDirectory (acOldPath, NUM_ELEMENTS_OF (acOldPath)))  // 备份当前路径成功?
    {
        MSetCurrentDirectory (szPath);  // 将当前路径修改到库文件所处目录
        blpDirChanged = TRUE;
    }
    else
    {
        blpDirChanged = FALSE;
    }

#if defined (_PF_WINDOWS)
    const H_LIB hLib = (H_LIB)::LoadLibrary (szLibraryName);
#elif defined (_PF_LINUX)
    const H_LIB hLib = (H_LIB)dlopen (szLibraryName, RTLD_NOW/*RTLD_LAZY*/);
#else
    #error unkown platform.
#endif

    // 恢复原当前目录
    if (blpDirChanged)
        MSetCurrentDirectory (acOldPath);

    return hLib;
}

BOOL_P MFreeLibrary (const H_LIB hLibraryModule)
{
    ASSERT (hLibraryModule != 0);

#if defined (_PF_WINDOWS)
    return (BOOL_P)::FreeLibrary ((HMODULE)hLibraryModule);
#elif defined (_PF_LINUX)
    return (dlclose ((void*)hLibraryModule) == 0);
#endif
}

VOID_FUNC MGetProcAddress (const H_LIB hLibraryModule, const U8CHAR* szProcName)
{
    ASSERT (hLibraryModule != 0);

#if defined (_PF_WINDOWS)
    return (VOID_FUNC)::GetProcAddress ((HMODULE)hLibraryModule, szProcName);
#elif defined (_PF_LINUX)
    return (VOID_FUNC)dlsym ((void*)hLibraryModule, szProcName);
#endif
}

//-------------------------------------------------------------

#ifdef _PF_WINDOWS

static HKEY GetRegistryKey (const TCHAR* szSection)
{
    ASSERT_R_STR (szSection);
    ASSERT (IsEmptyStr (szSection) == FALSE);

    HKEY hSoftKey;
    if (::RegOpenKeyEx (HKEY_CURRENT_USER, _T ("software"), 0, (KEY_WRITE | KEY_READ), &hSoftKey) == ERROR_SUCCESS)
    {
        HKEY hKey;
        if (::RegCreateKeyEx (hSoftKey, szSection, 0, REG_NONE,
                REG_OPTION_NON_VOLATILE, (KEY_WRITE | KEY_READ), NULL, &hKey, NULL) == ERROR_SUCCESS)
        {
            RegCloseKey (hSoftKey);
            return hKey;
        }

        RegCloseKey (hSoftKey);
    }

    return NULL;
}

BOOL_P MGetProfileBinary (const TCHAR* szSection, const TCHAR* szEntry, CVolMem* pMem)
{
    ASSERT_R_STR (szSection);
    ASSERT_R_STR (szEntry);
    ASSERT_RW_DATA (pMem);
    ASSERT (IsEmptyStr (szSection) == FALSE && IsEmptyStr (szEntry) == FALSE);

    pMem->Empty ();

    const HKEY hSecKey = GetRegistryKey (szSection);
    if (hSecKey == NULL)
        return FALSE;

    DWORD dwType, dwCount;
    LONG lResult = RegQueryValueEx (hSecKey, (TCHAR*)szEntry, NULL, &dwType, NULL, &dwCount);
    if (lResult == ERROR_SUCCESS)
    {
        ASSERT (dwType == REG_BINARY);
        lResult = RegQueryValueEx (hSecKey, (TCHAR*)szEntry, NULL, &dwType, pMem->Alloc ((INT_P)dwCount), &dwCount);
    }

    RegCloseKey (hSecKey);
    return (lResult == ERROR_SUCCESS);
}

BOOL_P MSetProfileBinary (const TCHAR* szSection, const TCHAR* szEntry, const BYTE* pData, const DWORD dwBytes)
{
    ASSERT_R_STR (szSection);
    ASSERT_R_STR (szEntry);
    ASSERT_R_ADR (pData, (INT_P)dwBytes);
    ASSERT (IsEmptyStr (szSection) == FALSE && IsEmptyStr (szEntry) == FALSE);

    const HKEY hSecKey = GetRegistryKey (szSection);
    if (hSecKey == NULL)
        return FALSE;

    const LONG lResult = RegSetValueEx (hSecKey, szEntry, NULL, REG_BINARY, pData, dwBytes);

    RegCloseKey (hSecKey);
    return (lResult == ERROR_SUCCESS);
}

BOOL_P MGetProfileBinary (const TCHAR* szSection, const TCHAR* szEntry, CVolMem* pMem, const INT_P npRequiredSize)
{
    ASSERT_R_STR (szSection);
    ASSERT_R_STR (szEntry);
    ASSERT_RW_DATA (pMem);

    if (MGetProfileBinary (szSection, szEntry, pMem) == FALSE)
        return FALSE;

    return (pMem->GetSize () == npRequiredSize);
}

void GetMonitorRect (const HWND hWnd, RECT* prtMonitor)
{
    ASSERT_RW_DATA (prtMonitor);

    if (hWnd != NULL)
    {
        const HMONITOR hMonitor = MonitorFromWindow (hWnd, MONITOR_DEFAULTTONEAREST);

        if (hMonitor != NULL)
        {
            MONITORINFO inf;
            inf.cbSize = sizeof (MONITORINFO);

            if (GetMonitorInfo (hMonitor, &inf))
            {
                COPY_MEM (prtMonitor, &inf.rcMonitor, sizeof (RECT));
                return;
            }
        }
    }

    prtMonitor->left = 0;
    prtMonitor->top = 0;
    prtMonitor->right = GetSystemMetrics (SM_CXSCREEN);
    prtMonitor->bottom = GetSystemMetrics (SM_CYSCREEN);
}

void CenterWindowInsideMonitor (const HWND hWnd, const INT_P npWindowWidth, const INT_P npWindowHeight)
{
    ASSERT (hWnd != NULL && npWindowWidth >= 0 && npWindowHeight >= 0);

    HWND hParentWnd = ::GetParent (hWnd);
    if (hParentWnd == NULL)
        hParentWnd = hWnd;

    // 获取父窗口所处显示器屏幕区域
    RECT rtMonitor;
    GetMonitorRect (hParentWnd, &rtMonitor);

    ::MoveWindow (hWnd,
            (rtMonitor.left + rtMonitor.right - (INT)npWindowWidth) / 2,
            (rtMonitor.top + rtMonitor.bottom - (INT)npWindowHeight) / 2,
            (INT)npWindowWidth, (INT)npWindowHeight, TRUE);
}

COLORREF MulRGB (const COLORREF clr, const DOUBLE dbMulValue)
{
    const INT_P r = GetClipValue ((INT_P)(dbMulValue * (DOUBLE)(UINT_P)GetRValue (clr) + 0.5), (INT_P)0, (INT_P)255);
    const INT_P g = GetClipValue ((INT_P)(dbMulValue * (DOUBLE)(UINT_P)GetGValue (clr) + 0.5), (INT_P)0, (INT_P)255);
    const INT_P b = GetClipValue ((INT_P)(dbMulValue * (DOUBLE)(UINT_P)GetBValue (clr) + 0.5), (INT_P)0, (INT_P)255);

    return RGB (r, g, b);
}

HINSTANCE MLoadSystemLibrary (const TCHAR* szLibPureFileName)
{
    if (IsEmptyStr (szLibPureFileName))
        return NULL;

    TCHAR acLoadPath [MAX_PATH + 1];
    const UINT rc = ::GetSystemDirectory (acLoadPath, NUM_ELEMENTS_OF (acLoadPath));
    if (rc == 0 || rc >= NUM_ELEMENTS_OF (acLoadPath))
        return NULL;

    CVolString strPath (acLoadPath);
    strPath.CheckAddPathChar ();
    strPath.AddText (szLibPureFileName);

    return ::LoadLibrary (strPath.GetText ());
}

#ifdef _DEBUG

void TrackWinLastError ()
{
    const DWORD dwLastError = ::GetLastError ();

    LPVOID lpMsgBuf; 
    ::FormatMessage (FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS, 
            NULL, dwLastError, MAKELANGID (LANG_NEUTRAL, SUBLANG_DEFAULT), // Default language 
            (TCHAR*)&lpMsgBuf, 0, NULL); 

    TRACE2 (_T ("LastError(%u): %s"), dwLastError, (const TCHAR*)lpMsgBuf);

    LocalFree (lpMsgBuf); 
}

#endif
#endif

void ReverseBytes (BYTE* pbData, const INT_P npDataSize)
{
    ASSERT_RW_ADR (pbData, npDataSize);

    BYTE bt;
    BYTE* pbFirst = pbData;
    BYTE* pbLast = pbFirst + npDataSize;

    for (; pbFirst != pbLast && pbFirst != --pbLast; ++pbFirst)
    {
        ASSERT (pbFirst >= pbData && pbFirst < pbData + npDataSize &&
                pbLast >= pbData && pbLast < pbData + npDataSize);

        bt = *pbLast;
        *pbLast = *pbFirst;
        *pbFirst = bt;
    }
}

WORD ReverseWordBytes (const WORD wValue)
{
    return (WORD)(((wValue & 0x00FF) << 8) | ((wValue & 0xFF00) >> 8));
}

DWORD ReverseDWordBytes (const DWORD dwValue)
{
    DWORD dwResult = ((dwValue & 0x000000FF) << 24);
    dwResult |= ((dwValue & 0x0000FF00) << 8);
    dwResult |= ((dwValue & 0x00FF0000) >> 8);
    dwResult |= ((dwValue & 0xFF000000) >> 24);

    return dwResult;
}

const CHAR* GetMbsText (const WCHAR* szText, CVolMem& memBuf, INT_P* pnpResultTextLength)
{
    ASSERT_R_STR (szText);

    if (pnpResultTextLength != NULL)
    {
        ASSERT_RW_DATA (pnpResultTextLength);
        *pnpResultTextLength = 0;
    }

    if (IsEmptyStr (szText) == FALSE)
    {
        const INT_P npLenIncludeEndZero = wcslen (szText) + 1;  // 获得包括结束零字符的待转换文本长度
        INT_P npBufLen = ::WideCharToMultiByte (CP_ACP, 0, szText, (INT)npLenIncludeEndZero, NULL, 0, NULL, NULL);

        CHAR* psBuf = (CHAR*)memBuf.Alloc (npBufLen * (INT_P)sizeof (CHAR));
        npBufLen = ::WideCharToMultiByte (CP_ACP, 0, szText, (INT)npLenIncludeEndZero, psBuf, (INT)npBufLen, NULL, NULL);

        if (npBufLen > 0)  // 转换成功?
        {
            ASSERT (npBufLen <= memBuf.GetSize () / (INT_P)sizeof (CHAR) &&
                    psBuf [npBufLen - 1] == '\0' && strlen (psBuf) == npBufLen - 1);  // npBufLen包括结束零字符

            if (pnpResultTextLength != NULL)
            {
                ASSERT_RW_DATA (pnpResultTextLength);
                *pnpResultTextLength = npBufLen - 1;
            }
            return psBuf;
        }
    }

    return "";
}

const WCHAR* GetWideText (const CHAR* szText, CVolMem& memBuf, INT_P* pnpResultTextLength)
{
    ASSERT_R_STR (szText);

    if (pnpResultTextLength != NULL)
    {
        ASSERT_RW_DATA (pnpResultTextLength);
        *pnpResultTextLength = 0;
    }

    if (IsEmptyStr (szText) == FALSE)
    {
        const INT_P npLenIncludeEndZero = strlen (szText) + 1;  // 获得包括结束零字符的待转换文本长度
        INT_P npBufLen = ::MultiByteToWideChar (CP_ACP, 0, szText, (INT)npLenIncludeEndZero, NULL, 0);

        WCHAR* pwsBuf = (WCHAR*)memBuf.Alloc (npBufLen * (INT_P)sizeof (WCHAR));
        npBufLen = ::MultiByteToWideChar (CP_ACP, 0, szText, (INT)npLenIncludeEndZero, pwsBuf, (INT)npBufLen);

        if (npBufLen > 0)  // 转换成功?
        {
            ASSERT (npBufLen <= memBuf.GetSize () / (INT_P)sizeof (WCHAR) &&
                    pwsBuf [npBufLen - 1] == '\0' && wcslen (pwsBuf) == npBufLen - 1);  // npBufLen包括结束零字符

            if (pnpResultTextLength != NULL)
            {
                ASSERT_RW_DATA (pnpResultTextLength);
                *pnpResultTextLength = npBufLen - 1;
            }
            return pwsBuf;
        }
    }

    return L"";
}

void XorData (void* pData, const INT_P npDataSize, const DWORD dwXorValue)
{
    ASSERT_RW_ADR (pData, npDataSize);

    if (dwXorValue == 0)
        return;  // 异或0值不会有任何改变

    // 首先以DWORD为单位进行异或
    DWORD* pdwData = (DWORD*)pData;
    const INT_P npNumDWords = npDataSize / sizeof (DWORD);
    for (INT_P npIndex = 0; npIndex < npNumDWords; npIndex++)
        *pdwData++ ^= dwXorValue;

    // 对剩余的字节进行异或
    const BYTE* pbXorValue = (const BYTE*)&dwXorValue;
    INT_P npNumBytes = (npDataSize % sizeof (DWORD));
    BYTE* pbData = (BYTE*)pdwData;
    for (; npNumBytes > 0; npNumBytes--)
        *pbData++ ^= *pbXorValue++;

    ASSERT (pbData == (const BYTE*)pData + npDataSize &&
            pbXorValue <= (const BYTE*)&dwXorValue + sizeof (DWORD));
}

DWORD GetDataXorValue (const void* pData, const INT_P npDataSize)
{
    ASSERT_R_ADR (pData, npDataSize);

    DWORD dwXorValue = 0;

    // 首先以DWORD为单位进行异或
    const DWORD* pdwData = (const DWORD*)pData;
    const INT_P npNumDWords = npDataSize / sizeof (DWORD);
    for (INT_P npIndex = 0; npIndex < npNumDWords; npIndex++)
        dwXorValue ^= *pdwData++;

    // 对剩余的字节进行异或
    BYTE* pbXorValue = (BYTE*)&dwXorValue;
    INT_P npNumBytes = (npDataSize % sizeof (DWORD));
    const BYTE* pbData = (const BYTE*)pdwData;
    for (; npNumBytes > 0; npNumBytes--)
        *pbXorValue++ ^= *pbData++;

    ASSERT (pbData == (const BYTE*)pData + npDataSize &&
            pbXorValue <= (const BYTE*)&dwXorValue + sizeof (DWORD));

    return dwXorValue;
}

BOOL_P WriteDataIntoFile (const TCHAR* szFileName, const void* pData, const INT_P npDataSize)
{
    ASSERT_R_STR (szFileName);
    ASSERT_R_ADR (pData, npDataSize);

    if (IsEmptyStr (szFileName) || npDataSize < 0)
        return FALSE;

    FILE* out = _tfopen (szFileName, _T ("wb"));
    if (out == NULL)
        return FALSE;

    const BOOL_P blpSucceeded = (fwrite (pData, 1, npDataSize, out) == npDataSize);

    fclose (out);
    return blpSucceeded;
}

#ifdef _PF_WINDOWS

SIZE GetTextDrawSize (HFONT hFont, const TCHAR* szText)
{
    ASSERT_R_STR (szText);

    SIZE size;
    size.cx = size.cy = 0;

    if (IsEmptyStr (szText) == FALSE)
    {
        if (hFont == NULL)
            hFont = (HFONT)::GetStockObject (DEFAULT_GUI_FONT);

        const HDC hDC = GetDC (NULL);
        const HFONT hOldFont = (HFONT)::SelectObject (hDC, hFont);

        VERIFY (::GetTextExtentPoint32 (hDC, szText, (INT)_tcslen (szText), &size));

        ::SelectObject (hDC, hOldFont);
        ::ReleaseDC (NULL, hDC);
    }

    return size;
}

HMODULE GetSelfModuleHandle ()
{
    MEMORY_BASIC_INFORMATION mbi;
    return (::VirtualQuery (GetSelfModuleHandle, &mbi, sizeof (mbi)) != 0 ? (HMODULE)mbi.AllocationBase : NULL);
}

DOUBLE DoubleFontDpSize2Pt (const DOUBLE dbFontDpSize)
{
    const HDC hDC = ::GetDC (NULL);
    const INT_P npLogY = ::GetDeviceCaps (hDC, LOGPIXELSY);
    ::ReleaseDC (NULL, hDC);

    return (npLogY != 0 ? fabs (dbFontDpSize) * 72.0 / (DOUBLE)npLogY : 0);
}

DOUBLE DoubleFontPtSize2Dp (const DOUBLE dbFontPtSize)
{
    const HDC hDC = ::GetDC (NULL);
    const DOUBLE dbDpSize = fabs (dbFontPtSize) * (DOUBLE)::GetDeviceCaps (hDC, LOGPIXELSY) / 72.0;
    ::ReleaseDC (NULL, hDC);

    return dbDpSize;
}

void GetDefaultFontInfo (LOGFONT* pinfFont)
{
    ASSERT (pinfFont != NULL);

    VERIFY_NOT_EQUAL (::GetObject (::GetStockObject (DEFAULT_GUI_FONT), sizeof (LOGFONT), pinfFont), 0);  // 必定成功
    pinfFont->lfHeight = -(LONG)DoubleFontPtSize2Dp (9);  // 使用9 pt作为字体单位(当涉及到多显示器且其中有一个显示器设定了非100%的dpi缩放比时,会导致另一个显示器所获取的字体尺寸出错)
}

void GetFontDescTextInfo (const TCHAR* szFontDescText, LOGFONT* pinfFont)
{
    ASSERT_R_STR (szFontDescText);
    ASSERT_RW_DATA (pinfFont);

    // 使用默认GUI字体的信息进行初始化
    VERIFY_NOT_EQUAL (::GetObject (::GetStockObject (DEFAULT_GUI_FONT), sizeof (LOGFONT), pinfFont), 0);  // 必定成功

    pinfFont->lfCharSet = DEFAULT_CHARSET;
    pinfFont->lfOutPrecision = OUT_DEFAULT_PRECIS;
    pinfFont->lfClipPrecision = CLIP_DEFAULT_PRECIS;
    pinfFont->lfQuality = PROOF_QUALITY;
    pinfFont->lfPitchAndFamily = DEFAULT_PITCH;

    // 分离各个部分
    CMStringArray sary;
    INT_P npCount = SplitStrings (szFontDescText, sary, ',', TRUE, FALSE);
    if (npCount > 7)
        npCount = 7;

    for (INT_P npIndex = 0; npIndex < npCount; npIndex++)
    {
        const TCHAR* ps = sary [npIndex];
        const BOOL_P bl = (ps [0] == '1' && ps [1] == '\0');  // 获得是否为逻辑值真

        switch (npIndex)
        {
        case 0:  // 字体名
            if (IsEmptyStr (ps) == FALSE)
                _tcsncpy_z (pinfFont->lfFaceName, ps, NUM_ELEMENTS_OF (pinfFont->lfFaceName) - 1);
            break;
        case 1:  {  // 字体尺寸
            const INT_P npFontSize = FontPtSize2Dp (_ttoi (ps));
            if (npFontSize > 0)  // 字体尺寸有效?
                pinfFont->lfHeight = (LONG)-npFontSize;  // (LONG)npFontSize;
            break;  }
        case 2:  // 是否为粗体
            pinfFont->lfWeight = (bl ? FW_BOLD : FW_NORMAL);
            break;
        case 3:  // 是否为斜体
            pinfFont->lfItalic = (BYTE)bl;
            break;
        case 4:  // 是否有下划线
            pinfFont->lfUnderline = (BYTE)bl;
            break;
        case 5:  // 是否有删除线
            pinfFont->lfStrikeOut = (BYTE)bl;
            break;
        case 6:  // 旋转角度
            if (IsEmptyStr (ps) == FALSE)
            {
                INT_P npAngle = (_ttoi (ps) % 3600);
                if (npAngle < 0)
                    npAngle += 3600;
                pinfFont->lfEscapement = pinfFont->lfOrientation = (LONG)npAngle;
            }
            break;
        }
    }
}

const TCHAR* GetFontDescText (const LOGFONT& infFont, CVolString& strFontDesc)
{
    strFontDesc.Empty ();

    // 记录字体名
    if (_tcschr (infFont.lfFaceName, ',') == NULL)  // 字体名内不能包括用作分隔的逗号字符
        strFontDesc.AddText (infFont.lfFaceName);

    // 记录字体尺寸
    TCHAR buf [32];
    strFontDesc.AddText (_T (", "));
    strFontDesc.AddText (n2str ((INT)FontDpSize2Pt (infFont.lfHeight), buf));

    // 记录其它字体信息
    strFontDesc.AddText (infFont.lfWeight >= FW_BOLD ? _T (", 1") : _T (", 0"));
    strFontDesc.AddText (infFont.lfItalic != 0 ? _T (", 1") : _T (", 0"));
    strFontDesc.AddText (infFont.lfUnderline != 0 ? _T (", 1") : _T (", 0"));
    strFontDesc.AddText (infFont.lfStrikeOut != 0 ? _T (", 1") : _T (", 0"));
    strFontDesc.AddText (_T (", "));
    strFontDesc.AddIntText ((INT)infFont.lfEscapement);

    return strFontDesc.GetText ();
}

BOOL_P IsValidAddress (const void* p, const INT_P npSize, const BOOL_P blpReadWrite)
{
    ASSERT (npSize >= 0);

    if (npSize == 0)
        return TRUE;

    return (p != NULL &&
            IsBadReadPtr (p, (UINT_PTR)npSize) == FALSE &&
            (blpReadWrite == FALSE || IsBadWritePtr ((LPVOID)p, (UINT_PTR)npSize) == FALSE));
}

INT MGetStretchMode ()
{
    DEVMODE dm;
    if (EnumDisplaySettings (NULL, ENUM_CURRENT_SETTINGS, &dm))
    {
        if (dm.dmBitsPerPel > 16)
            return HALFTONE;
    }

    return COLORONCOLOR;
}

#include <ShellAPI.h>

INT GetCommandLineArray (CMStringArray& saryArgs)
{
    saryArgs.RemoveAll ();

    INT nNumArgs = 0;
    LPWSTR* aszArglist = CommandLineToArgvW (GetCommandLineW (), &nNumArgs);
    if (aszArglist != NULL)
    {
        for (INT_P npIndex = 1; npIndex < (INT_P)nNumArgs; npIndex++)
            saryArgs.Add (aszArglist [npIndex]);

        GlobalFree (aszArglist);
    }
    
    /* const TCHAR* psCommand = SkipSpaces (GetCommandLine ());

    // 跳过调用程序名
    TCHAR ch = ' ';
    if (*psCommand == '\"')
    {
        ch = '\"';
        psCommand++;
    }
    while (*psCommand != ch && *psCommand != '\0')
        psCommand++;

    if (*psCommand != '\0')
        psCommand++;

    if (ch != ' ' && *psCommand == ' ')
        psCommand++;    // 跳过第一个空格。

    while (*psCommand != '\0')
    {
        if (*psCommand == '\"')
        {
            psCommand++;

            const TCHAR* ps = psCommand;
            while (*ps != '\0' && *ps != '\"')
                ps++;

            saryArgs.Add (psCommand, ps - psCommand);

            psCommand = ps;
            if (*psCommand != '\0')
                psCommand++;
        }
        else if ((UINT_P)*psCommand > (UINT_P)' ')
        {
            const TCHAR* ps = psCommand;
            while (*ps != '\0' && *ps != '\"' && (UINT_P)*ps > (UINT_P)' ')
                ps++;

            saryArgs.Add (psCommand, ps - psCommand);
            psCommand = ps;
        }
        else
        {
            psCommand++;
        }
    } */

    return (INT)saryArgs.GetCount ();
}

static BOOL sSetPrivilege ()
{
    OSVERSIONINFO osv;
    ZERO_MEM (&osv, sizeof (OSVERSIONINFO));
    osv.dwOSVersionInfoSize = sizeof (OSVERSIONINFO);
    GetVersionEx (&osv);

    if (osv.dwPlatformId == VER_PLATFORM_WIN32_NT)
    {
        HANDLE hToken; 
        TOKEN_PRIVILEGES tkp; 

        if (!OpenProcessToken (GetCurrentProcess (), (TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY), &hToken)) 
            return FALSE;

        LookupPrivilegeValue (NULL, SE_SHUTDOWN_NAME, &tkp.Privileges [0].Luid); 

        tkp.PrivilegeCount = 1;
        tkp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED; 
        AdjustTokenPrivileges (hToken, FALSE, &tkp, 0, (PTOKEN_PRIVILEGES)NULL, 0); 

        if (GetLastError () != ERROR_SUCCESS) 
            return FALSE;
    }

    return TRUE;
}

BOOL_P ExitWindowSystem (const INT_P npMode, const BOOL_P blpForceExit)
{
    if (npMode < 1 || npMode > 5 || sSetPrivilege () == FALSE)
        return FALSE;

    if (npMode >= 4)
        return SetSystemPowerState ((npMode == 4), (BOOL)blpForceExit);

    UINT uFlags;
    if (npMode == 1)
    {
        OSVERSIONINFO osv;
        ZERO_MEM (&osv, sizeof (OSVERSIONINFO));
        osv.dwOSVersionInfoSize = sizeof (OSVERSIONINFO);
        GetVersionEx (&osv);
        if (osv.dwPlatformId == VER_PLATFORM_WIN32_NT)
            uFlags = EWX_POWEROFF;
        else
            uFlags = EWX_SHUTDOWN;
    }
    else
    {
        uFlags = (npMode == 2 ? EWX_REBOOT : EWX_LOGOFF);
    }

    if (blpForceExit)
        uFlags |= EWX_FORCE;

    return ExitWindowsEx (uFlags, 0);
}

BOOL_P GetImageListItemSize (const HBITMAP hBitmap, SIZE* psizeItem)
{
    ASSERT (psizeItem != NULL);

    BITMAP bm;
    if (hBitmap == NULL ||
            ::GetObject (hBitmap, sizeof (BITMAP), &bm) == 0 ||
            bm.bmHeight == 0)
    {
        return FALSE;
    }

    const INT nImageWidth = (INT)((DWORD)(bm.bmHeight + 1) & 0xFFFFFFFE);  // 向上取偶
    psizeItem->cx = nImageWidth;
    psizeItem->cy = (INT)bm.bmHeight;

    return TRUE;
}

#endif

static INT s_int_compare_ascend (const void *elem1, const void *elem2)
{
    return (*(INT*)elem1 > *(INT*)elem2 ? 1 :
            *(INT*)elem1 < *(INT*)elem2 ? -1 :
            0);
}

static INT s_int_compare_descend (const void *elem1, const void *elem2)
{
    return (*(INT*)elem1 > *(INT*)elem2 ? -1 :
            *(INT*)elem1 < *(INT*)elem2 ? 1 :
            0);
}

void MSortIntArray (INT* pnArray, const INT_P npNumElements, const BOOL_P blpAscend)
{
    qsort (pnArray, (INT)npNumElements, sizeof (INT), (blpAscend ? s_int_compare_ascend : s_int_compare_descend));
}

static INT s_double_compare_ascend (const void *elem1, const void *elem2)
{
    return (*(DOUBLE*)elem1 > *(DOUBLE*)elem2 ? 1 :
            *(DOUBLE*)elem1 < *(DOUBLE*)elem2 ? -1 :
            0);
}

static INT s_double_compare_descend (const void *elem1, const void *elem2)
{
    return (*(DOUBLE*)elem1 > *(DOUBLE*)elem2 ? -1 :
            *(DOUBLE*)elem1 < *(DOUBLE*)elem2 ? 1 :
            0);
}

void MSortDoubleArray (DOUBLE* pdbArray, const INT_P npNumElements, const BOOL_P blpAscend)
{
    qsort (pdbArray, (INT)npNumElements, sizeof (DOUBLE), (blpAscend ? s_double_compare_ascend : s_double_compare_descend));
}

static const TCHAR* cs_szTraditionalNumber = _T ("零壹贰叁肆伍陆柒捌玖");
static const TCHAR* cs_szTraditionalUnit = _T ("拾佰仟万拾佰仟亿拾佰仟万");
static const TCHAR* cs_szSimpleNumber = _T ("零一二三四五六七八九");
static const TCHAR* cs_szSimpleUnit = _T ("十百千万十百千亿十百千万");
static const TCHAR* cs_szOverflow = _T ("溢出");
static const TCHAR cs_chDot = _T ('点');
static const TCHAR cs_chNeg = _T ('负');
static const TCHAR cs_chInt = _T ('整');
static const TCHAR cs_chYuan = _T ('元');
static const TCHAR cs_chFeng = _T ('分');
static const TCHAR cs_chJiao = _T ('角');

void NumberToCNText (DOUBLE dbNumber, const BOOL_P blpConvertToSimple, CVolString& strConvertResult)
{
    const TCHAR* szNumber;
    const TCHAR* szUnit;
    if (blpConvertToSimple)
    {
        szNumber = cs_szSimpleNumber;
        szUnit = cs_szSimpleUnit;
    }
    else
    {
        szNumber = cs_szTraditionalNumber;
        szUnit = cs_szTraditionalUnit;
    }

    TCHAR buf [128];
    TCHAR* psBuf = buf;

    const BOOL_P blpNeg = (dbNumber < 0);
    if (blpNeg)
        dbNumber = -dbNumber;

    if (IsDoubleEqualZero (dbNumber))
    {
        *psBuf = szNumber [0];
        psBuf [1] = '\0';
    }
    else if (dbNumber > 9999999999999.0)
    {
        _tcscpy (psBuf, cs_szOverflow);
    }
    else
    {
        psBuf = &buf [NUM_ELEMENTS_OF (buf) - 1];
        *psBuf = '\0';

        DOUBLE dbMod = modf (dbNumber, &dbNumber);
        dbMod *= 100;
        if (modf (dbMod + NEAR_ZERO_DOUBLE, &dbMod) >= 0.5)
            dbMod++;

        INT64 n64 = (INT64)dbNumber;
        INT_P npMod = (INT_P)dbMod;

        if (npMod >= 100)
        {
            n64++;
        }
        else if (npMod != 0)
        {
            TCHAR buf1 [32], buf2 [32];
            TCHAR* psNumber = (TCHAR*)np2str (npMod + 100, buf1);

            TCHAR* ps = psNumber + _tcslen (psNumber) - 1;
            psNumber [0] = '\0';
            while (*ps == '0')
                *ps-- = '\0';

            ps = psNumber + 1;
            INT_P npIndex = 0;
            while ((UINT_P)*ps >= (UINT_P)'0' && (UINT_P)*ps <= (UINT_P)'9')
            {
                buf2 [npIndex] = szNumber [(UINT_P)*ps - (UINT_P)'0'];
                npIndex++;
                ps++;
            }

            psBuf -= npIndex;
            COPY_MEM (psBuf, buf2, npIndex * sizeof (TCHAR));
            psBuf--;
            *psBuf = cs_chDot;
        }

        if (n64 == 0)
        {
            psBuf--;
            *psBuf = szNumber [0];
        }
        else
        {
            INT_P npZeroType = 0;  // 0:还没有任何数字; 1:最近一个是零; 2:最近一个是数字
            INT_P npIndex = 0, npMod;
            BOOL_P blpHaveUnit = FALSE;

            while (n64 > 0)
            {
                npMod = (INT_P)(n64 % 10);
                n64 /= 10;

                if (npIndex == 4 || npIndex == 8)
                    blpHaveUnit = FALSE;

                if (npMod == 0)
                {
                    if (npZeroType == 2)
                    {
                        psBuf--;
                        *psBuf = szNumber [0];
                        npZeroType = 1;
                    }
                }
                else
                {
                    npZeroType = 2;

                    if (npIndex > 0)
                    {
                        if (blpHaveUnit == FALSE && npIndex >= 4)
                        {
                            if (npIndex < 8)
                            {
                                if (npIndex > 4)
                                {
                                    psBuf--;
                                    *psBuf = szUnit [3];
                                }

                                blpHaveUnit = TRUE;
                            }
                            else
                            {
                                if (npIndex > 8)
                                {
                                    psBuf--;
                                    *psBuf = szUnit [7];
                                }

                                blpHaveUnit = TRUE;
                            }
                        }

                        psBuf--;
                        *psBuf = szUnit [npIndex - 1];
                    }

                    psBuf--;
                    *psBuf = szNumber [npMod];
                }

                npIndex++;
            }
        }

        if (blpNeg)
        {
            psBuf--;
            *psBuf = cs_chNeg;
        }
    }

    strConvertResult.SetText (psBuf);
}

void NumberToCurrency (DOUBLE dbNumber, const BOOL_P blpConvertToSimple, CVolString& strConvertResult)
{
    const TCHAR* szNumber;
    const TCHAR* szUnit;
    if (blpConvertToSimple)
    {
        szNumber = cs_szSimpleNumber;
        szUnit = cs_szSimpleUnit;
    }
    else
    {
        szNumber = cs_szTraditionalNumber;
        szUnit = cs_szTraditionalUnit;
    }

    TCHAR buf [128];
    TCHAR* psBuf = buf;

    const BOOL_P blpNeg = (dbNumber < 0);
    if (blpNeg)
        dbNumber = -dbNumber;

    if (IsDoubleEqualZero (dbNumber))
    {
        *psBuf = szNumber [0];
        psBuf [1] = '\0';
    }
    else if (dbNumber > 9999999999999.0)
    {
        _tcscpy (psBuf, cs_szOverflow);
    }
    else
    {
        psBuf = &buf [NUM_ELEMENTS_OF (buf) - 1];
        *psBuf = '\0';

        dbNumber *= 100;
        if (modf (dbNumber + NEAR_ZERO_DOUBLE, &dbNumber) >= 0.5)
            dbNumber++;
        INT64 n64 = (INT64)dbNumber;

        if ((n64 % 10) == 0)
        {
            psBuf--;
            *psBuf = cs_chInt;
        }

        INT_P npZeroType = 0;  // 0:还没有任何数字; 1:最近一个是零; 2:最近一个是数字
        INT_P npIndex = 0, npMod;
        BOOL_P blpHaveUnit = FALSE, blpHaveYuan = FALSE;

        while (n64 > 0)
        {
            npMod = n64 % 10;
            n64 /= 10;

            if (npIndex == 6 || npIndex == 10)
                blpHaveUnit = FALSE;

            if (npMod == 0)
            {
                if (npZeroType == 2)
                {
                    psBuf--;
                    *psBuf = szNumber [0];
                    npZeroType = 1;
                }
            }
            else
            {
                npZeroType = 2;

                if (npIndex < 2)
                {
                    psBuf--;
                    *psBuf = (npIndex == 0 ? cs_chFeng : cs_chJiao);
                }
                else
                {
                    if (blpHaveYuan == FALSE)
                    {
                        psBuf--;
                        *psBuf = cs_chYuan;
                        blpHaveYuan = TRUE;
                    }

                    if (blpHaveUnit == FALSE && npIndex >= 6)
                    {
                        if (npIndex < 10)
                        {
                            if (npIndex > 6)
                            {
                                psBuf--;
                                *psBuf = szUnit [3];
                            }

                            blpHaveUnit = TRUE;
                        }
                        else
                        {
                            if (npIndex > 10)
                            {
                                psBuf--;
                                *psBuf = szUnit [7];
                            }

                            blpHaveUnit = TRUE;
                        }
                    }

                    if (npIndex > 2)
                    {
                        psBuf--;
                        *psBuf = szUnit [npIndex - 3];
                    }
                }

                psBuf--;
                *psBuf = szNumber [npMod];
            }

            npIndex++;
        }

        if (blpNeg)
        {
            psBuf--;
            *psBuf = cs_chNeg;
        }
    }

    strConvertResult.SetText (psBuf);
}

void NumberToFormatText (DOUBLE dbNumber, const INT_P npFracKeepNumber, const BOOL_P blpTausendstelSeparation, CVolString& strConvertResult)
{
    if (npFracKeepNumber != INT_MAX)
        dbNumber = RoundDouble (dbNumber, npFracKeepNumber);

    TCHAR buf [128];
    _stprintf (buf, _T ("%.15G"), dbNumber);

    if (npFracKeepNumber != INT_MAX && npFracKeepNumber > 0)
    {
        TCHAR* ps =  _tcschr (buf, '.');

        if (ps == NULL)
        {
            ps = &buf [_tcslen (buf)];
            *ps++ = '.';
            for (INT_P npIndex = 0; npIndex < npFracKeepNumber; npIndex++)
                *ps++ = '0';
            *ps = '\0';
        }
        else
        {
            ps++;

            INT_P npFracNumber = 0;
            while (*ps != '\0')
            {
                npFracNumber++;
                ps++;
            }

            npFracNumber = npFracKeepNumber - npFracNumber;
            if (npFracNumber > 0)
            {
                for (INT_P npIndex = 0; npIndex < npFracNumber; npIndex++)
                    *ps++ = '0';
                *ps = '\0';
            }
        }
    }

    if (blpTausendstelSeparation)
    {
        TCHAR* psBegin = buf;
        if (*psBegin == '-')
            psBegin++;

        TCHAR* ps = psBegin;
        while (*ps != '\0')
        {
            const TCHAR ch = *ps++;
            if (ch != '.' && ((UINT_P)ch < (UINT_P)'0' || (UINT_P)ch > (UINT_P)'9'))
                break;
        }

        if (*ps == '\0')
        {
            TCHAR* psDot = _tcschr (buf, '.');
            if (psDot  == NULL)
                ps = buf + _tcslen (buf);
            else
                ps = psDot;

            while (TRUE)
            {
                ps -= 3;
                if (ps <= psBegin)
                    break;
                MOVE_MEM (ps + 1, ps, (_tcslen (ps) + 1) * sizeof (TCHAR));
                *ps = ',';
            }
        }
    }

    strConvertResult.SetText (buf);
}

#ifdef _PF_WINDOWS

// 从管道中读取宽文本数据,返回是否读取成功.
static BOOL_P sReadHandleContext (const HANDLE hPipe, const CONSOLE_APP_OUT_CHAR_SET enOutCharSet,
        CVolMem& memWideText, INT_P* pnpReadedDataSize)
{
    ASSERT (hPipe != NULL);

    //----------------------------------------------------------------------  删除过多的文本

    INT_P npOldSize = memWideText.GetSize ();

    #define _MAX_OUT_TEXT_DATA_SIZE  0xFFFF  // 最多允许的输出文本数据尺寸
    if (npOldSize > _MAX_OUT_TEXT_DATA_SIZE)  // 数据已经太多?
    {
        const WCHAR* pws = (const WCHAR*)memWideText.GetPtr ();
        const BYTE* pbNewBegin = (const BYTE*)pws + (npOldSize - _MAX_OUT_TEXT_DATA_SIZE);

        while ((const BYTE*)pws <= pbNewBegin)
        {
            const WCHAR* pwsNextLine = wcschr (pws, '\n');  // 寻找行尾的换行符
            if (pwsNextLine == NULL)
                break;
            pws = pwsNextLine + 1;  // 到下一行
        }

        // 获得删除数据尺寸
        const INT_P npRemoveSize = (const BYTE*)pws - memWideText.GetPtr ();
        if (npRemoveSize <= 0)  // 数据格式很特别导致删除数据尺寸为0?
            memWideText.Empty ();  // 全部清除. 注意: 会同时将尾部的'\0'字符清除,但是后面能够正常处理.
        else
            memWideText.Remove (0, npRemoveSize);

        npOldSize = memWideText.GetSize ();
    }

    //----------------------------------------------------------------------

    memWideText.RemoveEndZeroWChar ();  // 首先删除尾部可能存在的'\0'字符

    BYTE buf [1024];
    CVolMem memOutText;
    BOOL_P blpReadSucceeded = TRUE;  // 用作记录是否读取成功

    while (TRUE)
    {
        // 预先查看一下管道中是否存在数据,如果没有则不进行读取,以免后面的ReadFile调用阻塞.
        DWORD dwSize = 0;
        if (PeekNamedPipe (hPipe, NULL, 0, NULL, &dwSize, NULL) == FALSE)
        {
            // if (GetLastError () == ERROR_BROKEN_PIPE)  // 管道已经关闭?
            //     blpReadSucceeded = FALSE;
            blpReadSucceeded = FALSE;  // 返回读取失败(统一处理了管道已经关闭的情况)
            break;
        }
        
        if (dwSize == 0)  // 管道中不存在数据?
            break;

        // 实际读取管道数据
        dwSize = 0;
        if (ReadFile (hPipe, buf, sizeof (buf), &dwSize, NULL) == FALSE)
        {
            blpReadSucceeded = FALSE;  // 返回读取失败(统一处理了管道已经关闭的情况)
            break;
        }

        if (dwSize == 0)  // 管道中的现有数据已经读取完毕?
            break;

        // 有些程序会在中间输出莫名其妙的'\0'字符,如: powershell "Get-Partition -DiskNumber 1 | Select-Object PartitionNumber,DriveLetter,Size,Type", 在此将其转换为空格.
        ASSERT (enOutCharSet == CAOCS_MBS || enOutCharSet == CAOCS_UTF8);
        const INT_P npReadedSize = (INT_P)dwSize;
        for (INT_P npIndex = 0; npIndex < npReadedSize; npIndex++)
        {
            if (buf [npIndex] == '\0')
                buf [npIndex] = ' ';
        }

        // 先记录下来,放到读取完毕后统一转换编码,避免在半个字符处进行转换.
        memOutText.Append (buf, npReadedSize);
    }

    if (memOutText.IsEmpty () == FALSE)
    {
        memOutText.AddDWord (0);  // 加上结束'\0'字符

        CVolMem memBuf;
        const WCHAR* pws;
        switch (enOutCharSet)
        {
        case CAOCS_MBS:
            pws = GetWideText ((const CHAR*)memOutText.GetPtr (), memBuf, NULL);
            break;
        case CAOCS_UTF8:
            pws = Utf8ToWStr ((const U8CHAR*)memOutText.GetPtr (), -1, memBuf);
            break;
        default:
            FAIL;  // 没有其它编码格式了
            pws = L"";
            break;
        }

        // 添加到输出内存中
        if (IsEmptyStr (pws) == FALSE)
            memWideText.Append (pws, wcslen (pws) * sizeof (WCHAR));
    }

    if (pnpReadedDataSize != NULL)
        *pnpReadedDataSize = memWideText.GetSize () - npOldSize;

    memWideText.AddWChar ('\0');  // 加上文本结束'\0'字符
    return blpReadSucceeded;  // 返回是否读取成功
}

static TIME_OUT_CHECK_RESULT sTimeoutChecker (const TIME_OUT_CALL_BACK_PARAM* pCallbackParam)
{
    ASSERT (pCallbackParam != NULL && IsEmptyStr (pCallbackParam->m_szCommandLine) == FALSE &&
            pCallbackParam->m_upUserData1 > 0);

    if (pCallbackParam->m_blpProcessExited)  // 程序退出前的最后一次调用?
        return TOCR_EXIT;

    if ((UINT_P)pCallbackParam->m_dwRunningTime >= pCallbackParam->m_upUserData1)  // upUserData1中为最大允许的运行时间
        return TOCR_TIME_OUT;  // 返回超时

    return TOCR_CONTINUE;  // 返回继续执行
}

const TCHAR* sGetExecutableFilePathFromCommandLine (const TCHAR* szCommandLine, CVolString& strPath)
{
    strPath.Empty ();

    do
    {
        if (IsEmptyStr (szCommandLine))
            break;

        const TCHAR* ps = SkipSpaces (szCommandLine);
        const TCHAR* ps2;

        if (*ps == '\"')
        {
            ps++;
            ps2 = ps;

            while (TRUE)
            {
                const TCHAR ch = *ps2;
                if (ch == '\0' || ch == '\"')
                    break;
                ps2++;
            }

            if (*ps2 != '\"')  // 未找到回引号?
                break;
        }
        else
        {
            ps2 = ps;

            while (TRUE)
            {
                const TCHAR ch = *ps2;
                if (ch == '\0' || IS_SPACE_CHAR_NOT_CHECK_ZERO (ch))
                    break;
                ps2++;
            }
        }

        //----------------------------------------------------------------------

        CVolString str (ps, ps2 - ps);
        str.TrimAll ();

        return GetOSFilePathPart (str.GetText (), strPath);
    }
    while (FALSE);

    return strPath.GetText ();
}

CONSOLE_APP_RUN_RESULT RunConsoleAppWithTimeoutCheck (const TCHAR* szCommandLine, const TCHAR* szWorkingPath,
        const CONSOLE_APP_OUT_CHAR_SET enOutCharSet, CVolString* pstrStdOut, CVolString* pstrStdError,
        const BOOL_P blpRemoveAllEmptyLines, DWORD* pdwAppExitCode, const DWORD dwMaxWaitMillseconds)
{
    if (dwMaxWaitMillseconds == 0)
    {
        return RunConsoleApp (szCommandLine, szWorkingPath, enOutCharSet, pstrStdOut, pstrStdError,
                blpRemoveAllEmptyLines, pdwAppExitCode, NULL);
    }

    // 建立超时检查参数
    CONSOLE_APP_TIME_OUT_CHECK_PARAM pmTimeoutCheck;
    pmTimeoutCheck.m_fnIsTimeout = sTimeoutChecker;
    pmTimeoutCheck.m_upNotifyInterval = 1000;
    pmTimeoutCheck.m_upUserData1 = (UINT_P)dwMaxWaitMillseconds;  // 设置等待时间(毫秒)
    pmTimeoutCheck.m_upUserData2 = 0;

    return RunConsoleApp (szCommandLine, szWorkingPath, enOutCharSet, pstrStdOut, pstrStdError,
            blpRemoveAllEmptyLines, pdwAppExitCode, &pmTimeoutCheck);
}

CONSOLE_APP_RUN_RESULT RunConsoleAppWithEnv (const TCHAR* szEnvironmentData, const TCHAR* szCommandLine, const TCHAR* szWorkingPath,
        const CONSOLE_APP_OUT_CHAR_SET enOutCharSet, CVolString* pstrStdOut, CVolString* pstrStdError,
        const BOOL_P blpRemoveAllEmptyLines, DWORD* pdwAppExitCode, const CONSOLE_APP_TIME_OUT_CHECK_PARAM* pTimeoutCheckParam)
{
    // 首先初始化返回结果
    if (pstrStdOut != NULL)  pstrStdOut->Empty ();
    if (pstrStdError != NULL)  pstrStdError->Empty ();
    if (pdwAppExitCode != NULL)  *pdwAppExitCode = (DWORD)-1;

    if (IsEmptyStr (szCommandLine))
        return CARR_FAIL;

    // 定义并初始化相关句柄
    HANDLE hStdOutRead, hStdOutWrite, hStdErrorRead, hStdErrorWrite;
    hStdOutRead = hStdOutWrite = hStdErrorRead = hStdErrorWrite = NULL;

    PROCESS_INFORMATION pi;
    ZERO_MEM (&pi, sizeof (pi));

    // 以下变量仅当pTimeoutCheckParam不为NULL时有效
    DWORD dwTimeStartup;  // 用作记录起始运行时间
    DWORD dwNotifyInterval;  // 用作记录通知间隔毫秒数
    DWORD dwTimeLastNotify;  // 用作记录上一次的通知时间

    if (pTimeoutCheckParam != NULL)  // 指定了超时检查参数?
    {
        if (pTimeoutCheckParam->m_fnIsTimeout == NULL)
        {
            FAIL;  // 按照规范不能为NULL
            pTimeoutCheckParam = NULL;
        }
        else
        {
            dwTimeStartup = ::GetTickCount ();
            dwNotifyInterval = (DWORD)pTimeoutCheckParam->m_upNotifyInterval;
            dwTimeLastNotify = dwTimeStartup;
        }
    }

    //--------------------------------------------------------------------------

    CONSOLE_APP_RUN_RESULT enResult = CARR_FAIL;  // 用作记录操作结果
    BOOL_P blpProcessRunning = FALSE;  // 用作标志程序是否正在运行

    do
    {
        SECURITY_ATTRIBUTES sa;
        ZERO_MEM (&sa, sizeof (sa));
        sa.nLength = sizeof (sa);
        sa.bInheritHandle = TRUE;  // 设置句柄继承标志

        // 创建标准输入输出句柄管道
        if (pstrStdOut != NULL &&  // 需要获取标准输出信息?
                CreatePipe (&hStdOutRead, &hStdOutWrite, &sa, 0) == FALSE)
        {
            hStdOutRead = hStdOutWrite = NULL;
            break;
        }

        // 创建错误输入输出句柄管道
        if (pstrStdError != NULL &&  // 需要获取标准错误输出信息?
                CreatePipe (&hStdErrorRead, &hStdErrorWrite, &sa, 0) == FALSE)
        {
            hStdErrorRead = hStdErrorWrite = NULL;
            break;
        }

        // 建立程序启动信息
        STARTUPINFO si;
        ZERO_MEM (&si, sizeof (si));
        si.cb = sizeof (si);
        si.dwFlags = (STARTF_USESHOWWINDOW | STARTF_USESTDHANDLES);
        si.wShowWindow = SW_HIDE;
        if (pstrStdOut != NULL)
        {
            ASSERT (hStdOutWrite != NULL);
            si.hStdOutput = hStdOutWrite;  // 重定位标准输出
        }
        if (pstrStdError != NULL)
        {
            ASSERT (hStdErrorWrite != NULL);
            si.hStdError = hStdErrorWrite;  // 重定位错误输出
        }

        blpProcessRunning = TRUE;  // 设置程序处于正在运行状态

        DWORD dwCreationFlags = 0/*CREATE_NEW_PROCESS_GROUP*/;
        if (szEnvironmentData != NULL)  // 提供了环境数据?
            dwCreationFlags |= CREATE_UNICODE_ENVIRONMENT;

        // 启动程序
        CVolString strPath;
        CVolMem memCommandLine;
        memCommandLine.AddString (szCommandLine);
        if (CreateProcess (NULL, (TCHAR*)memCommandLine.GetTextPtr (),
                NULL, NULL, TRUE, dwCreationFlags, (LPVOID)szEnvironmentData,
                (szWorkingPath == NULL ? NULL :  // 使用调用进程的当前目录?
                    *szWorkingPath == '\0' ? sGetExecutableFilePathFromCommandLine (szCommandLine, strPath) :  // 自动从szCommandLine中获取?
                    szWorkingPath),  // 使用所指定的目录
                &si, &pi) == FALSE)
        {
            pi.hProcess = NULL;
            break;
        }

        //   这几个句柄已经被继承到被启动的进程中去了,由该进程输出信息时使用,此处需要将其关闭,
        // 不然会导致下面的ReadFile死锁.
        if (pstrStdOut != NULL)
        {
            ASSERT (hStdOutWrite != NULL);
            CloseHandle (hStdOutWrite);
            hStdOutWrite = NULL;
        }
        if (pstrStdError != NULL)
        {
            ASSERT (hStdErrorWrite != NULL);
            CloseHandle (hStdErrorWrite);
            hStdErrorWrite = NULL;
        }

        //--------------------------------------------------------------------------

        enResult = CARR_SUCCEEDED;  // 设置为执行成功

        CVolMem memStdOutWideText, memStdErrorWideText;  // 用作存放所读取的宽文本数据
        if (pstrStdOut != NULL || pTimeoutCheckParam != NULL)  // 需要标准输出数据或提供有超时检查参数?
            memStdOutWideText.AddWChar ('\0');  // 加上文本结束'\0'字符
        if (pstrStdError != NULL || pTimeoutCheckParam != NULL)  // 需要标准错误输出数据或提供有超时检查参数?
            memStdErrorWideText.AddWChar ('\0');

        TIME_OUT_CALL_BACK_PARAM pmTimeout;
        TIME_OUT_CHECK_RESULT enTimeoutCheckResult = TOCR_CONTINUE;
        if (pTimeoutCheckParam != NULL)  // 提供有超时检查参数?
        {
            pmTimeout.m_szCommandLine = szCommandLine;
            pmTimeout.m_pmemStdOutWideText = &memStdOutWideText;
            pmTimeout.m_pmemStdErrorWideText = &memStdErrorWideText;
            pmTimeout.m_upUserData1 = pTimeoutCheckParam->m_upUserData1;
            pmTimeout.m_upUserData2 = pTimeoutCheckParam->m_upUserData2;
            pmTimeout.m_blpProcessExited = FALSE;
        }

        INT_P npReadedStdoutDataSize, npReadedStdErrorDataSize;

        do
        {
            // 等待程序执行一段时间
            if (blpProcessRunning)  // 程序仍在运行?
            {
                if (WaitForSingleObject (pi.hProcess, 100) != WAIT_TIMEOUT)  // 程序执行完毕?
                {
                    blpProcessRunning = FALSE;  // 设置程序已经退出标志
                }
                else if (pTimeoutCheckParam != NULL)  // 提供有超时检查参数?
                {
                    const DWORD dwCurrentTime = GetTickCount ();  // 获得当前时间
                    ASSERT (dwCurrentTime >= dwTimeLastNotify);  // 正常情况下必定满足此条件

                    if (dwCurrentTime - dwTimeLastNotify >= dwNotifyInterval)  // 到了通知周期?
                    {
                        dwTimeLastNotify = dwCurrentTime;  // 更新最后通知时间

                        ASSERT (pTimeoutCheckParam->m_fnIsTimeout != NULL &&  // 前面检查过
                                dwCurrentTime >= dwTimeStartup);  // 正常情况下必定满足此条件
                        pmTimeout.m_dwRunningTime = dwCurrentTime - dwTimeStartup;

                        // 必定都以'\0'结束
                        ASSERT (memStdOutWideText.EndWCharOf ('\0') &&
                                memStdErrorWideText.EndWCharOf ('\0'));

                        enTimeoutCheckResult = pTimeoutCheckParam->m_fnIsTimeout (&pmTimeout);

                        // 如果修改后不以WCHAR字符尺寸结束,则将其对齐.
                        INT_P npSize = (memStdOutWideText.GetSize () % sizeof (WCHAR));
                        if (npSize != 0)
                            memStdOutWideText.RemoveToEnd (memStdOutWideText.GetSize () - npSize);
                        npSize = (memStdErrorWideText.GetSize () % sizeof (WCHAR));
                        if (npSize != 0)
                            memStdErrorWideText.RemoveToEnd (memStdErrorWideText.GetSize () - npSize);

                        // 如果修改后不以'\0'结束,则将其补上.
                        if (memStdOutWideText.EndWCharOf ('\0') == FALSE)
                            memStdOutWideText.AddWChar ('\0');
                        if (memStdErrorWideText.EndWCharOf ('\0') == FALSE)
                            memStdErrorWideText.AddWChar ('\0');

                        if (enTimeoutCheckResult == TOCR_EXIT)  // 返回退出?
                            break;

                        if (enTimeoutCheckResult == TOCR_TIME_OUT)  // 返回超时?
                        {
                            enResult = CARR_TIMEOUT;  // 设置为超出最大等待时间
                            break;
                        }
                    }
                }
            }

            // 读入标准输出数据
            npReadedStdoutDataSize = 0;
            if (pstrStdOut != NULL)
                sReadHandleContext (hStdOutRead, enOutCharSet, memStdOutWideText, &npReadedStdoutDataSize);

            // 读入标准错误输出数据
            npReadedStdErrorDataSize = 0;
            if (pstrStdError != NULL)
                sReadHandleContext (hStdErrorRead, enOutCharSet, memStdErrorWideText, &npReadedStdErrorDataSize);
        }
        while (npReadedStdoutDataSize > 0 || npReadedStdErrorDataSize > 0 || blpProcessRunning);  // 本次读入了有效管道数据或者程序仍旧在运行?

        if (pTimeoutCheckParam != NULL &&  // 提供有超时检查参数?
                enTimeoutCheckResult == TOCR_CONTINUE)  // 不为超时检查中退出的?
        {
            ASSERT (blpProcessRunning == FALSE);  // 前面的算法决定

            pmTimeout.m_dwRunningTime = GetTickCount () - dwTimeStartup;
            pmTimeout.m_blpProcessExited = TRUE;
            pTimeoutCheckParam->m_fnIsTimeout (&pmTimeout);  // 最后调用一次
        }

        // 将所获得的标准输出多字节文本转换后返回
        if (pstrStdOut != NULL)
        {
            ASSERT (memStdOutWideText.EndWCharOf ('\0'));  // 必定以'\0'字符结束

            pstrStdOut->SetText ((const WCHAR*)memStdOutWideText.GetPtr ());
        }

        // 将所获得的标准错误输出多字节文本转换后返回
        if (pstrStdError != NULL)
        {
            ASSERT (memStdErrorWideText.EndWCharOf ('\0'));  // 必定以'\0'字符结束

            if (pstrStdError == pstrStdOut)  // 两者指向同一个接收对象?
            {
                if (pstrStdError->IsEmpty () == FALSE)  // 存在标准输出文本?
                    pstrStdError->AddText (_T ("\r\n"));  // 在其后添加一个换行
                pstrStdError->AddText ((const WCHAR*)memStdErrorWideText.GetPtr ());
            }
            else
            {
                pstrStdError->SetText ((const WCHAR*)memStdErrorWideText.GetPtr ());
            }
        }

        // 获得程序返回值
        if (pdwAppExitCode != NULL)
        {
            if (enResult == CARR_TIMEOUT)  // 超出最大等待时间?
            {
                *pdwAppExitCode = (DWORD)-1;
            }
            else if (GetExitCodeProcess (pi.hProcess, pdwAppExitCode) == FALSE)
            {
                *pdwAppExitCode = 0;
            }
        }
    }
    while (FALSE);

    //--------------------------------------------------------------------------
    // 关闭所有句柄

    if (pi.hProcess != NULL)
    {
        if (blpProcessRunning)  // 程序仍然在运行?
        {
            // 发送中断信号
            GenerateConsoleCtrlEvent (CTRL_C_EVENT, pi.dwProcessId);
            GenerateConsoleCtrlEvent (CTRL_BREAK_EVENT, pi.dwProcessId);

            const HANDLE hProcess = OpenProcess (PROCESS_TERMINATE, FALSE, pi.dwProcessId);
            if (hProcess != NULL)
            {
                TerminateProcess (hProcess, -1);  // 强行终止该进程
                CloseHandle (hProcess);
            }
        }

        CloseHandle (pi.hThread);
        CloseHandle (pi.hProcess);
    }

    if (hStdOutRead != NULL)  CloseHandle (hStdOutRead);
    if (hStdOutWrite != NULL)  CloseHandle (hStdOutWrite);
    if (hStdErrorRead != NULL)  CloseHandle (hStdErrorRead);
    if (hStdErrorWrite != NULL)  CloseHandle (hStdErrorWrite);

    if (blpRemoveAllEmptyLines)  // 需要删除输出信息中的空白行?
    {
        if (pstrStdOut != NULL)
            pstrStdOut->RemoveAllSpaceLines ();

        if (pstrStdError != NULL && pstrStdError != pstrStdOut)
            pstrStdError->RemoveAllSpaceLines ();
    }

    return enResult;
}

BOOL_P RunCommandLine (const TCHAR* szCommandLine, const BOOL_P blpWaitEnd, const INT_P npShowWindow, LPDWORD pdwExitCode, CVolString* pstrStdOut, CVolString* pstrStdError, const BOOL_P blpStdOutUTF8)
{
    ASSERT_R_STR (szCommandLine);

    if (pdwExitCode != NULL)
        *pdwExitCode = (blpWaitEnd ? (DWORD)-1 : 0);

    if (pstrStdOut != NULL)
        pstrStdOut->Empty ();

    if (pstrStdError != NULL)
        pstrStdError->Empty ();

    if (IsEmptyStr (szCommandLine))
        return FALSE;

    // 创建输入输出句柄管道
    HANDLE hStdOutRead, hStdOutWrite, hStdErrorRead, hStdErrorWrite;
    hStdOutRead = hStdOutWrite = hStdErrorRead = hStdErrorWrite = NULL;
    if (blpWaitEnd && (pstrStdOut != NULL || pstrStdError != NULL))  // 等待进程执行完毕且需要获取标准输出信息?
    {
        SECURITY_ATTRIBUTES sa;
        ZERO_MEM (&sa, sizeof (sa));
        sa.nLength = sizeof (sa);
        sa.bInheritHandle = TRUE;  // 设置句柄继承标志

        if (pstrStdOut != NULL && CreatePipe (&hStdOutRead, &hStdOutWrite, &sa, 0) == FALSE)
            hStdOutRead = hStdOutWrite = NULL;

        if (pstrStdError != NULL && CreatePipe (&hStdErrorRead, &hStdErrorWrite, &sa, 0) == FALSE)
            hStdErrorRead = hStdErrorWrite = NULL;
    }

    //-----------------------------------------------------------------------------

    STARTUPINFO infStartup;
    ZERO_MEM (&infStartup, sizeof (infStartup));
    infStartup.cb = sizeof (infStartup);

    if (npShowWindow >= 0)
    {
        infStartup.dwFlags |= STARTF_USESHOWWINDOW;
        infStartup.wShowWindow = (WORD)npShowWindow;
    }

    if (hStdOutWrite != NULL || hStdErrorWrite != NULL)
    {
        infStartup.dwFlags |= STARTF_USESTDHANDLES;

        infStartup.hStdInput = GetStdHandle (STD_INPUT_HANDLE);
        infStartup.hStdOutput = (hStdOutWrite != NULL ? hStdOutWrite : GetStdHandle (STD_OUTPUT_HANDLE));
        infStartup.hStdError = (hStdErrorWrite != NULL ? hStdErrorWrite : GetStdHandle (STD_ERROR_HANDLE));
    }

    PROCESS_INFORMATION pi;
    CVolMem memCommandLine;
    memCommandLine.AddString (szCommandLine);
    const BOOL_P blpProcessCreateSucceeded = CreateProcess (NULL, (TCHAR*)memCommandLine.GetPtr (), NULL, NULL, TRUE, 0, NULL, NULL, &infStartup, &pi);

    // 这些句柄已经被继承到被启动的进程中去了,由该进程输出信息时使用,此处需要将其关闭,不然会导致下面的ReadFile死锁.
    if (hStdOutWrite != NULL)  CloseHandle (hStdOutWrite);
    if (hStdErrorWrite != NULL)  CloseHandle (hStdErrorWrite);

    if (blpProcessCreateSucceeded == FALSE)
    {
        if (hStdOutRead != NULL)  CloseHandle (hStdOutRead);
        if (hStdErrorRead != NULL)  CloseHandle (hStdErrorRead);

        return FALSE;
    }

    if (blpWaitEnd == FALSE)
    {
        ASSERT (hStdOutWrite == NULL && hStdErrorWrite == NULL);

        WaitForInputIdle (pi.hProcess, 500);
    }
    else
    {
        if (hStdOutRead == NULL && hStdErrorRead == NULL)
        {
            WaitForSingleObject (pi.hProcess, INFINITE);
        }
        else
        {
            CVolMem memStdOut, memStdError;
            DWORD dwReadedStdOutDataSize = 0, dwReadedStdErrorDataSize = 0;
            BOOL_P blpProcessRunning = TRUE;
            BYTE buf [0x1000];

            do
            {
                // 等待程序执行一段时间
                if (blpProcessRunning)  // 程序仍在运行?
                {
                    if (WaitForSingleObject (pi.hProcess, 100) != WAIT_TIMEOUT)  // 程序执行完毕?
                        blpProcessRunning = FALSE;  // 设置程序已经退出标志
                }

                // 读入标准输出数据
                if (hStdOutRead != NULL)
                {
                    if (ReadFile (hStdOutRead, buf, sizeof (buf) - 1, &dwReadedStdOutDataSize, NULL) == FALSE)
                        dwReadedStdOutDataSize = 0;
                    else
                        memStdOut.Append (buf, (INT_P)(UINT_P)dwReadedStdOutDataSize);
                }

                // 读入标准错误输出数据
                if (hStdErrorRead != NULL)
                {
                    if (ReadFile (hStdErrorRead, buf, sizeof (buf) - 1, &dwReadedStdErrorDataSize, NULL) == FALSE)
                        dwReadedStdErrorDataSize = 0;
                    else
                        memStdError.Append (buf, (INT_P)(UINT_P)dwReadedStdErrorDataSize);
                }
            }
            while (dwReadedStdOutDataSize > 0 || dwReadedStdErrorDataSize > 0 || blpProcessRunning);  // 本次读入了有效管道数据或者程序仍旧在运行?

            //-----------------------------------------------------------------------------

            if (hStdOutRead != NULL)
            {
                ASSERT (pstrStdOut != NULL);

                CloseHandle (hStdOutRead);
                memStdOut.AddDWord (0);  // 加上结束'\0'字符

                CVolMem memBuf;
                pstrStdOut->SetText (blpStdOutUTF8 ?  // UTF8编码?
                        Utf8ToWStr ((const U8CHAR*)memStdOut.GetPtr (), -1, memBuf) :
                        GetWideText ((const CHAR*)memStdOut.GetPtr (), memBuf, NULL));
            }

            if (hStdErrorRead != NULL)
            {
                ASSERT (pstrStdError != NULL);

                CloseHandle (hStdErrorRead);
                memStdError.AddDWord (0);  // 加上结束'\0'字符

                CVolMem memBuf;
                pstrStdError->SetText (blpStdOutUTF8 ?  // UTF8编码?
                        Utf8ToWStr ((const U8CHAR*)memStdError.GetPtr (), -1, memBuf) :
                        GetWideText ((const CHAR*)memStdError.GetPtr (), memBuf, NULL));
            }
        }

        if (pdwExitCode != NULL)
            GetExitCodeProcess (pi.hProcess, pdwExitCode);
    }

    //-----------------------------------------------------------------------------

    CloseHandle (pi.hThread);
    CloseHandle (pi.hProcess);
    return TRUE;

/* Old code:
    ASSERT_R_STR (szCommandLine);

    if (IsEmptyStr (szCommandLine))
        return FALSE;

    STARTUPINFO infStartup;
    ZERO_MEM (&infStartup, sizeof (infStartup));
    infStartup.cb = sizeof (infStartup);

    if (npShowWindow >= 0)
    {
        infStartup.dwFlags |= STARTF_USESHOWWINDOW;
        infStartup.wShowWindow = (WORD)npShowWindow;
    }

    PROCESS_INFORMATION pi;
    CVolMem memCommandLine;
    memCommandLine.AddString (szCommandLine);
    if (CreateProcess (NULL, (TCHAR*)memCommandLine.GetPtr (), NULL, NULL, FALSE, 0, NULL, NULL, &infStartup, &pi) == FALSE)
        return FALSE;

    if (blpWaitEnd)
        WaitForSingleObject (pi.hProcess, INFINITE);
    else
        WaitForInputIdle (pi.hProcess, 500);

    CloseHandle (pi.hThread);
    CloseHandle (pi.hProcess);
    return TRUE; */
}

CONSOLE_APP_RUN_RESULT RunConsoleAppAndWrapLines (const TCHAR* szCommandLine, const TCHAR* szWorkingPath,
        const CONSOLE_APP_OUT_CHAR_SET enOutCharSet, CMStringArray* psaryStdOutLines, CMStringArray* psaryStdErrorLines,
        const BOOL_P blpRemoveAllEmptyLines, DWORD* pdwAppExitCode, const CONSOLE_APP_TIME_OUT_CHECK_PARAM* pTimeoutCheckParam)
{
    CVolString strStdOut, strStdError;

    const CONSOLE_APP_RUN_RESULT enResult = RunConsoleApp (
            szCommandLine, szWorkingPath, enOutCharSet, 
            (psaryStdOutLines == NULL ? NULL : &strStdOut),
            (psaryStdErrorLines == NULL ? NULL : &strStdError),
            blpRemoveAllEmptyLines, pdwAppExitCode, pTimeoutCheckParam);

    if (enResult != CARR_SUCCEEDED)
    {
        if (psaryStdOutLines != NULL)
            psaryStdOutLines->RemoveAll ();

        if (psaryStdErrorLines != NULL)
            psaryStdErrorLines->RemoveAll ();
    }
    else
    {
        // 自动根据换行符分行
        if (psaryStdOutLines != NULL)
            SplitStrings (strStdOut.GetText (), *psaryStdOutLines, '\n', TRUE, TRUE);

        if (psaryStdErrorLines != NULL)
            SplitStrings (strStdError.GetText (), *psaryStdErrorLines, '\n', TRUE, TRUE);
    }

    return enResult;
}

typedef struct
{
    DWORD m_dwCurrentProcessId;
    HWND m_hExcludeWnd;
    BOOL_P m_blpHasTopWindow;
}
_EnumTopWindowsParam;

static BOOL CALLBACK sEnumTopWindowsCallBack (HWND hWnd, LPARAM lParam)  
{
    _EnumTopWindowsParam* pParam = (_EnumTopWindowsParam*)lParam;
    ASSERT (pParam != NULL);

    if (pParam->m_hExcludeWnd != hWnd)
    {
        DWORD dwPid = 0;  
        GetWindowThreadProcessId (hWnd, &dwPid);  // 获得找到窗口所属的进程  

        if (dwPid == pParam->m_dwCurrentProcessId)
        {
            pParam->m_blpHasTopWindow = TRUE;
            return FALSE;
        }
    }

    return TRUE;
}

BOOL_P IsCurrentProcessHasTopWindow (const HWND hExcludeWnd)
{
    _EnumTopWindowsParam param;
    param.m_dwCurrentProcessId = GetCurrentProcessId ();
    param.m_hExcludeWnd = hExcludeWnd;
    param.m_blpHasTopWindow = FALSE;

    EnumWindows (sEnumTopWindowsCallBack, (LPARAM)&param);
    return param.m_blpHasTopWindow;
}

INT_P GetNumProcessorsInsideSystem ()
{
    SYSTEM_INFO si;
    ::GetSystemInfo (&si);
    return (INT_P)si.dwNumberOfProcessors;
}

INT_P GetRecommendWorkingThreadCount (const INT_P npMaxThreadCount)
{
    // 根据计算机中当前CPU计算核心的数目计算推荐工作线程的数目,最多不超过npMaxThreadCount个.
    const INT_P npNumThreads = GetNumProcessorsInsideSystem () * 2 + 2;

    if (npMaxThreadCount > 0 && npNumThreads > npMaxThreadCount)
        return npMaxThreadCount;

    return npNumThreads;
}

void MyDragAcceptFiles (HWND hWnd, BOOL_P blpEnable)
{
    if (hWnd == NULL)
        return;

    ::DragAcceptFiles (hWnd, (BOOL)blpEnable);

    typedef BOOL (WINAPI *PFN_ChangeWindowMessageFilterEx) (HWND hwnd, UINT message, DWORD action, void* pChangeFilterStruct);
    PFN_ChangeWindowMessageFilterEx fn = (PFN_ChangeWindowMessageFilterEx)::GetProcAddress (
            ::GetModuleHandle (_T ("User32.dll")), "ChangeWindowMessageFilterEx");

    if (fn != NULL)
    {
        const DWORD dwAction = (blpEnable ? 1 : 0);  // MSGFLT_ALLOW: 1;  MSGFLT_RESET: 0

        fn (hWnd, WM_DROPFILES, dwAction, NULL);
        fn (hWnd, WM_COPYDATA, dwAction, NULL);
        fn (hWnd, 0x49, dwAction, NULL);  // WM_COPYGLOBALDATA
    }
}

#endif

void DebugTrace (const BOOL_P blpStringFormatText, const INT nMaxDumpSize, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, ...)
{
#ifdef _DEBUG
    va_list argList;
    va_start (argList, szParamTypes);

    CVolString strDebug (_T_VOL_DEBUG_OUT_STRING_LEADER);
    AddDebugDumpString (blpStringFormatText, nMaxDumpSize, npFirstExtendParamTypeIndex, szParamTypes, strDebug, argList);
    
    if (strDebug.GetLength () > 0x3FFF)
    {
        DEBUG_PRINT (strDebug.Left (0x3FFF).GetText ());
    }
    else
    {
        strDebug.AddText (_T ("\r\n"));
        DEBUG_PRINT (strDebug.GetText ());
    }

    va_end (argList);
#endif
}

void DebugTraceWithSourcePos (const TCHAR* szSourceFileName, const TCHAR* szLineNumber, const BOOL_P blpStringFormatText,
        const INT nMaxDumpSize, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, ...)
{
#ifdef _DEBUG
    va_list argList;
    va_start (argList, szParamTypes);

    CVolString strDebug (_T_VOL_DEBUG_OUT_STRING_LEADER);

    if (IsEmptyStr (szSourceFileName) == FALSE && IsEmptyStr (szLineNumber) == FALSE)
    {
        const INT_P npLineNumber = _ttoi (szLineNumber);

        if (npLineNumber >= 1)
            strDebug.AddFormatText (_T ("<%s>, %d: "), szSourceFileName, (INT)npLineNumber);
    }

    AddDebugDumpString (blpStringFormatText, nMaxDumpSize, npFirstExtendParamTypeIndex, szParamTypes, strDebug, argList);
    
    if (strDebug.GetLength () > 0x3FFF)
        DEBUG_PRINT (strDebug.Left (0x3FFF).GetText ());
    else
        DEBUG_PRINT (strDebug.GetText ());

    va_end (argList);
#endif
}

void DebugMessageBox (const BOOL_P blpStringFormatText, const INT nMaxDumpSize, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, ...)
{
#ifdef _DEBUG
    va_list argList;
    va_start (argList, szParamTypes);

    CVolString strDebug;
    ::MessageBox (NULL, AddDebugDumpString (blpStringFormatText, nMaxDumpSize, npFirstExtendParamTypeIndex, szParamTypes, strDebug, argList), _T_DEBUG_MSG_BOX_CAPTION, MB_OK);

    va_end (argList);
#endif
}

CVolString& DebugGetDumpString (const BOOL_P blpStringFormatText, const INT nMaxDumpSize, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, CVolString* pstrDebug, ...)
{
    ASSERT (pstrDebug != NULL);

    pstrDebug->Empty ();

#ifdef _DEBUG
    va_list argList;
    va_start (argList, pstrDebug);

    AddDebugDumpString (blpStringFormatText, nMaxDumpSize, npFirstExtendParamTypeIndex, szParamTypes, *pstrDebug, argList);

    va_end (argList);
#endif

    return *pstrDebug;
}

const TCHAR* AddDebugDumpString (const BOOL_P blpStringFormatText, const INT nMaxDumpSize, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, CVolString& strDebug, va_list argList)
{
    ASSERT (npFirstExtendParamTypeIndex >= 0);
    ASSERT_R_STR (szParamTypes);

#ifdef _DEBUG
    const INT_P npNumParams = _tcslen (szParamTypes);
    ASSERT (npNumParams >= npFirstExtendParamTypeIndex);

    for (INT_P npParamIndex = npFirstExtendParamTypeIndex; npParamIndex < npNumParams; npParamIndex++)
    {
        if (npParamIndex > npFirstExtendParamTypeIndex)
            strDebug.AddText (_T (", "));

        switch (szParamTypes [npParamIndex])
        {
        case _C_VOL_SBYTE:  // 字节
            strDebug.AddIntText ((INT)va_arg (argList, S_BYTE));
            break;
        case _C_VOL_SHORT:  // 短整数
            strDebug.AddIntText ((INT)va_arg (argList, SHORT));
            break;
        case _C_VOL_WCHAR:  // 字符
            strDebug.AddChar (va_arg (argList, TCHAR));
            break;
        case _C_VOL_INT:  // 整数
            strDebug.AddIntText (va_arg (argList, INT));
            break;
        case _C_VOL_VINT:  // 变整数
            strDebug.AddIntPText (va_arg (argList, INT_P));
            break;
        case _C_VOL_METHOD:  // 方法名
        case _C_NATIVE_REF_DATA_TYPE:  // 本地参考类型
        case _C_NATIVE_CLASS:  // 本地类(所有对象数据类型由于定义了"req_obj_param_pointer"属性都为指针,下同)?
        case _C_NATIVE_STRUCT:  {
            TCHAR buf [64];
            buf [0] = '0';
            buf [1] = 'x';
            UPToHexStr (va_arg (argList, UINT_P), sizeof (UINT_P) * 2, &buf [2], NUM_ELEMENTS_OF (buf) - 2);
            strDebug.AddText (buf);
            break;  }
        case _C_VOL_LONG:  // 长整数
            strDebug.AddInt64Text (va_arg (argList, INT64));
            break;
        case _C_VOL_FLOAT:  // 单精度小数
            strDebug.AddFloatText ((FLOAT)va_arg (argList, DOUBLE));  // FLOAT在VC中是使用DOUBLE方式传递的
            break;
        case _C_VOL_DOUBLE:  // 小数
            strDebug.AddDoubleText (va_arg (argList, DOUBLE));
            break;
        case _C_VOL_BOOL:  // 逻辑值
            strDebug.AddText (va_arg (argList, BOOL) ? _T_V_TRUE : _T_V_FALSE);
            break;
        case _C_VOL_STRING:  {  // 文本型
            // 文本型由于定义了"req_str_param_text_pointer"所以为指针
            const TCHAR* ps = va_arg (argList, const TCHAR*);
            if (blpStringFormatText)  // 以字符串格式输出文本?
            {
                CVolString str;
                strDebug.AddText (MakeStringFromPlainText (ps, &str, TRUE));
            }
            else
                strDebug.AddText (ps);
            break;  }
        case _C_VOL_CLASS:  {
            // 所有对象数据类型由于定义了"req_obj_param_pointer"属性都为指针.
            CVolString strBuf;
            va_arg (argList, CVolObject*)->GetDumpString (strBuf, nMaxDumpSize);  // 调用对应对象的取展示内容方法
            strDebug.AddText (strBuf);
            break;  }
        default:
            strDebug.AddText (_T ("???"));
            npParamIndex = npNumParams;  // 由于没有前进指针,无法再继续.
            break;
        }
    }
#endif

    return strDebug.GetText ();
}

CVolMem& CollectVariantVolDatas (CVolMem& memData, const TCHAR* szParamTypes, ...)
{
    va_list argList;
    va_start (argList, szParamTypes);

    CollectVariantListVolDatas (memData, szParamTypes, argList);

    va_end (argList);
    return memData;
}

CVolMem& CollectVariantListVolDatas (CVolMem& memData, const TCHAR* szParamTypes, va_list argList)
{
    ASSERT_R_STR (szParamTypes);

    memData.Empty ();

    const INT_P npNumParams = _tcslen (szParamTypes);
    for (INT_P npParamIndex = 0; npParamIndex < npNumParams; npParamIndex++)
    {
        switch (szParamTypes [npParamIndex])
        {
        case _C_VOL_SBYTE:  // 字节
            memData.AddByte ((BYTE)va_arg (argList, S_BYTE));
            break;
        case _C_VOL_SHORT:  // 短整数
            memData.AddWord ((WORD)va_arg (argList, SHORT));
            break;
        case _C_VOL_WCHAR:  // 字符
            memData.AddChar (va_arg (argList, TCHAR));
            break;
        case _C_VOL_INT:  // 整数
            memData.AddInt (va_arg (argList, INT));
            break;
        case _C_VOL_VINT:  // 变整数
        case _C_VOL_METHOD:  // 方法名
        case _C_NATIVE_REF_DATA_TYPE:  // 本地参考类型
            memData.AddIntP (va_arg (argList, INT_P));
            break;
        case _C_VOL_LONG:  // 长整数
            memData.AddInt64 (va_arg (argList, INT64));
            break;
        case _C_VOL_FLOAT:  // 单精度小数
            memData.AddFloat ((FLOAT)va_arg (argList, DOUBLE));  // FLOAT在VC中是使用DOUBLE方式传递的
            break;
        case _C_VOL_DOUBLE:  // 小数
            memData.AddDouble (va_arg (argList, DOUBLE));
            break;
        case _C_VOL_BOOL:  // 逻辑值
            memData.AddBool (va_arg (argList, BOOL));
            break;
        case _C_VOL_STRING:  // 文本型
            // 文本型由于定义了"req_str_param_text_pointer"所以为指针
            memData.AddString (va_arg (argList, const TCHAR*));
            break;
        case _C_VOL_CLASS:  {
            // 所有对象数据类型由于定义了"req_obj_param_pointer"属性都为指针.
            const CVolObject* pVolObject = va_arg (argList, CVolObject*);
            if (P_IS_VOL_INSTANCE_OF (pVolObject, CVolMem))
                memData.Append (((CVolMem*)pVolObject)->GetPtr (), ((CVolMem*)pVolObject)->GetSize ());
            break;  }
        }
    }

    return memData;
}

INT_P GetImageFileMachineType (const TCHAR* szFileName)
{
    INT_P npMachineType = IMAGE_FILE_MACHINE_UNKNOWN;

    FILE* pFile = _tfopen (szFileName, _T ("rb"));
    if (pFile != NULL)
    {
        IMAGE_DOS_HEADER header;
        DWORD dwSignature;
        WORD wMachine;

        if (fread (&header, 1, sizeof (header), pFile) == sizeof (header) &&
                fseek (pFile, header.e_lfanew, SEEK_SET) == 0 &&
                fread (&dwSignature, 1, sizeof (dwSignature), pFile) == sizeof (dwSignature) &&
                dwSignature == IMAGE_NT_SIGNATURE &&
                fread (&wMachine, 1, sizeof (wMachine), pFile) == sizeof (wMachine))
        {
            npMachineType = (INT_P)(UINT_P)wMachine;
        }

        fclose (pFile);
    }

    return npMachineType;
}

IMAGE_FILE_MACHINE_BITS_COUNT GetImageFileMachineBits (const TCHAR* szFileName)
{
    const INT_P npMachineType = GetImageFileMachineType (szFileName);

    return (npMachineType == IMAGE_FILE_MACHINE_I386 ? IFMBC_WIN32 :
            npMachineType == IMAGE_FILE_MACHINE_AMD64 ? IFMBC_X64 :
            IFMBC_UNKNOWN);
}

const TCHAR* GetEscapeChar (const TCHAR* psText, const TCHAR* psEndMark, TCHAR* pchResult)
{
    ASSERT (pchResult != NULL && psEndMark >= psText);

    if (psText >= psEndMark)
    {
        *pchResult = '\0';
        return psText;
    }

    if (*psText != '\\' ||  // 不为转义引导字符?
            psText + 1 == psEndMark)  // 文本长度为一个字符?
    {
        *pchResult = *psText;
        return psText + 1;
    }

    psText++;  // 跳过转义引导字符

    // 获得当前字符
    ASSERT (psText < psEndMark);  // 前面检查过
    const TCHAR chCurrent = *psText;
    psText++;

    switch (chCurrent)
    {
    case 'b':   *pchResult = '\b';  break;
    case 'f':   *pchResult = '\f';  break;
    case 'r':   *pchResult = '\r';  break;
    case 'n':   *pchResult = '\n';  break;
    case 't':   *pchResult = '\t';  break;
    case '\'':  *pchResult = '\'';  break;
    case '\"':  *pchResult = '\"';  break;
    case '\\':  *pchResult = '\\';  break;

    // 下面3个转义符java不支持,但是c和c++支持.
    // case 'a':   *pchResult = '\a';  break;
    // case 'v':   *pchResult = '\v';  break;
    // case '\?':  *pchResult = '\?';  break;  // 不必要

    case 'x':
    case 'u':  {  // 用作支持java转义符
        // 获得允许后跟的最多十六进制字符数目
        const INT_P npMaxNumHexChars = (chCurrent == 'x' ? 3 : 4);  // 'u'转义字符在java中后跟最多4个十六进制字符

        UINT_P upValue = 0;
        INT_P npIndex = 0;
        for ( ; npIndex < npMaxNumHexChars && psText < psEndMark; npIndex++, psText++)
        {
            const UINT_P upChar = *psText;

            if (IS_NUMBER_CHAR (upChar))
                upValue = ((upValue << 4) | (upChar - '0'));
            else if (upChar >= 'A' && upChar <= 'F')
                upValue = ((upValue << 4) | (upChar - 'A' + 10));
            else if (upChar >= 'a' && upChar <= 'f')
                upValue = ((upValue << 4) | (upChar - 'a' + 10));
            else
                break;
        }

        if (npIndex == 0)  // 后面一个有效的十六进制字符都没有?
            *pchResult = chCurrent;
        else
            *pchResult = (TCHAR)upValue;
        break;  }

    default:  {  // "\ooo"
        psText--;  // 退回到首八进制字符处

        UINT_P upValue = 0;
        INT_P npIndex = 0;
        for ( ; npIndex < 3 && psText < psEndMark; npIndex++, psText++)
        {
            const UINT_P upChar = *psText;

            if (upChar >= '0' && upChar <= '7')
                upValue = ((upValue << 3) | (upChar - '0'));
            else
                break;
        }

        if (npIndex == 0)  // 后面一个有效的八进制字符都没有?
            *pchResult = '\\';  // 首八进制字符前为'\\'转义引导字符
        else
            *pchResult = (TCHAR)upValue;
        break;  }
    }

    ASSERT (psText <= psEndMark);  // 前面的算法决定
    return psText;
}

const TCHAR* EscapeToPlainText (const TCHAR* psText, const TCHAR* psEndMark, CVolMem& memBuf)
{
    if (psText >= psEndMark)
        return _T ("");

    TCHAR* psBegin = (TCHAR*)memBuf.Alloc (sizeof (TCHAR) * (psEndMark - psText + 1));
    TCHAR* ps = psBegin;

    while (psText < psEndMark)
    {
        ASSERT (memBuf.IsInside (ps, sizeof (TCHAR)));
        psText = GetEscapeChar (psText, psEndMark, ps);
        ps++;
    }

    ASSERT (memBuf.IsInside (ps, sizeof (TCHAR)));
    *ps = '\0';
    return psBegin;
}

const TCHAR* PlainToEscapeText (const TCHAR* psText, const TCHAR* psEndMark, CVolMem& memBuf)
{
    if (psText >= psEndMark)
        return _T ("");

    // 基于极限情况分配内存,每个字符被转换为使用了4个字符的"\???"八进制转义字符.
    TCHAR* psBegin = (TCHAR*)memBuf.Alloc (sizeof (TCHAR) * (psEndMark - psText + 1) * 4);
    TCHAR* ps = psBegin;

    while (psText < psEndMark)
    {
        ASSERT (memBuf.IsInside (ps, sizeof (TCHAR) * 4));

        const UINT_P upChar = *psText++;

        TCHAR chEscape;
        switch (upChar)
        {
        case '\b':  chEscape = 'b';   break;
        case '\f':  chEscape = 'f';   break;
        case '\r':  chEscape = 'r';   break;
        case '\n':  chEscape = 'n';   break;
        case '\t':  chEscape = 't';   break;
        case '\'':  chEscape = '\'';  break;
        case '\"':  chEscape = '\"';  break;
        case '\\':  chEscape = '\\';  break;
        case '\0':  chEscape = '0';   break;
        // case '\a':  chEscape = 'a';  break;  // java不支持
        // case '\v':  chEscape = 'v';  break;  // java不支持
        // case '\?':  chEscape = '?';  break;  // java不支持,'?'号不需要.

        default:
            if (upChar >= ' ')  // 为可视字符?
            {
                *ps++ = (TCHAR)upChar;
            }
            else
            {
                // 使用转义字符值
                ps += _stprintf (ps, (upChar <= (UINT_P)0xFF ? _T ("\\x%02X") : _T ("\\u%04X")), (INT)(DWORD)upChar);
            }
            continue;
        }

        *ps++ = '\\';
        *ps++ = chEscape;
    }

    ASSERT (memBuf.IsInside (ps, sizeof (TCHAR)));
    *ps = '\0';
    return psBegin;
}

const TCHAR* MakeStringFromPlainText (const TCHAR* szPlainText, CVolString* pstrResult, const BOOL_P blpEncloseEmptyStr)
{
    ASSERT (pstrResult != NULL);

    CVolMem memBuf;
    const TCHAR* ps = PlainToEscapeText (szPlainText, memBuf);
    
    pstrResult->Empty ();

    if (IsEmptyStr (ps))
    {
        if (blpEncloseEmptyStr)
            pstrResult->SetText (_T ("\"\""));
    }
    else
    {
        pstrResult->AddChar ('\"');
        pstrResult->AddText (ps);
        pstrResult->AddChar ('\"');
    }

    return pstrResult->GetText ();
}

#define _VOL_CHOOSE_BASE_DATYA_TYPE_VALUE(data_type)  \
    ASSERT (npNumValues >= 1);  \
    npValueIndex = CLIP (npValueIndex, 0, npNumValues - 1);  \
    va_list argList;  \
    va_start (argList, npNumValues);  \
    data_type result = 0;  \
    for (INT_P npIndex = 0; npIndex <= npValueIndex; npIndex++)  \
        result = va_arg (argList, data_type);  \
    va_end (argList);  \
    return result;

S_BYTE ChooseOneValue_S_BYTE (INT_P npValueIndex, const INT_P npNumValues, ...)
{
    _VOL_CHOOSE_BASE_DATYA_TYPE_VALUE (S_BYTE)
}

SHORT ChooseOneValue_SHORT (INT_P npValueIndex, const INT_P npNumValues, ...)
{
    _VOL_CHOOSE_BASE_DATYA_TYPE_VALUE (SHORT)
}

TCHAR ChooseOneValue_TCHAR (INT_P npValueIndex, const INT_P npNumValues, ...)
{
    _VOL_CHOOSE_BASE_DATYA_TYPE_VALUE (TCHAR)
}

INT ChooseOneValue_INT (INT_P npValueIndex, const INT_P npNumValues, ...)
{
    _VOL_CHOOSE_BASE_DATYA_TYPE_VALUE (INT)
}

INT64 ChooseOneValue_INT64 (INT_P npValueIndex, const INT_P npNumValues, ...)
{
    _VOL_CHOOSE_BASE_DATYA_TYPE_VALUE (INT64)
}

FLOAT ChooseOneValue_FLOAT (INT_P npValueIndex, const INT_P npNumValues, ...)
{
    _VOL_CHOOSE_BASE_DATYA_TYPE_VALUE (FLOAT)
}

DOUBLE ChooseOneValue_DOUBLE (INT_P npValueIndex, const INT_P npNumValues, ...)
{
    _VOL_CHOOSE_BASE_DATYA_TYPE_VALUE (DOUBLE)
}

BOOL ChooseOneValue_BOOL (INT_P npValueIndex, const INT_P npNumValues, ...)
{
    _VOL_CHOOSE_BASE_DATYA_TYPE_VALUE (BOOL)
}

CVolString& ChooseOneValue_CVolString (INT_P npValueIndex, const INT_P npNumValues, ...)
{
    ASSERT (npNumValues >= 1);
    npValueIndex = CLIP (npValueIndex, 0, npNumValues - 1);

    va_list argList;
    va_start (argList, npNumValues);

    CVolString* result = NULL;
    for (INT_P npIndex = 0; npIndex <= npValueIndex; npIndex++)
        result = va_arg (argList, CVolString*);

    va_end (argList);
    ASSERT (result != NULL);  // 前面的算法决定
    return *result;
}

COLORREF OffsetColor (const COLORREF clr, INT_P npOffset)
{
    if (npOffset == 0 || npOffset < -255 || npOffset > 255)
        return clr;

    INT_P npOffsetR = npOffset;
    INT_P npOffsetG = npOffset;
    INT_P npOffsetB = npOffset;

    const INT_P npRed = (INT_P)(UINT_P)GetRValue (clr);
    const INT_P npGreen = (INT_P)(UINT_P)GetGValue (clr);
    const INT_P npBlue = (INT_P)(UINT_P)GetBValue (clr);

    if (npOffset > 0)
    {
        if (npRed + npOffset > 255)
            npOffsetR = 255 - npRed;
        if (npGreen + npOffset > 255)
            npOffsetG = 255 - npGreen;
        if (npBlue + npOffset > 255)
            npOffsetB = 255 - npBlue;

        npOffset = MIN3 (npOffsetR, npOffsetG, npOffsetB);
    }
    else
    {
        if (npRed + npOffset < 0)
            npOffsetR = -npRed;
        if (npGreen + npOffset < 0)
            npOffsetG = -npGreen;
        if (npBlue + npOffset < 0)
            npOffsetB = -npBlue;

        npOffset = MAX3 (npOffsetR, npOffsetG, npOffsetB);
    }

    return RGB (npRed + npOffset, npGreen + npOffset, npBlue + npOffset);
}

INT GetVolControlGroupNumber (HWND hControlWnd)
{
    INT nGroupNumber = -1;
    return ((hControlWnd != NULL && ::SendMessage (hControlWnd, MWM_GET_WND_GROUP_NUMBER, (WPARAM)&nGroupNumber, _VOL_MSG_ACK) == _VOL_MSG_ACK) ? nGroupNumber : -1);
}

BOOL SetVolControlGroupNumber (HWND hControlWnd, INT nNewGroupNumber)
{
    return (hControlWnd != NULL && ::SendMessage (hControlWnd, MWM_SET_WND_GROUP_NUMBER, (WPARAM)nNewGroupNumber, _VOL_MSG_ACK) == _VOL_MSG_ACK);
}

void NotifyParentCurrentChildTabChanged (HWND hTabWnd, const BOOL_P blpPostMessage)
{
    ASSERT (hTabWnd != NULL);

    HWND hParent = ::GetParent (hTabWnd);
    while (hParent != NULL)
    {
        if (blpPostMessage)
        {
            ::PostMessage (hParent, MWM_ON_CURRENT_CHILD_TAB_CHANGED, (WPARAM)hTabWnd, _VOL_MSG_ACK);
        }
        else
        {
            if (::SendMessage (hParent, MWM_ON_CURRENT_CHILD_TAB_CHANGED, (WPARAM)hTabWnd, _VOL_MSG_ACK) == _VOL_MSG_ACK)
                break;
        }

        hParent = ::GetParent (hParent);
    }
}

void ProcessCurrentChildTabChanged (HWND hTabWnd)
{
    INT nChildTabIndex = -1;

    if (hTabWnd != NULL &&
            ::SendMessage (hTabWnd, MWM_GET_CURRENT_CHILD_TAB_INDEX, (WPARAM)&nChildTabIndex, _VOL_MSG_ACK) == _VOL_MSG_ACK &&
            nChildTabIndex >= 0)
    {
        for (HWND hWndChild = ::GetWindow (hTabWnd, GW_CHILD);
                hWndChild != NULL;
                hWndChild = ::GetWindow (hWndChild, GW_HWNDNEXT))
        {
            const INT nGroupNumber = GetVolControlGroupNumber (hWndChild);
            if (nGroupNumber >= 0)
            {
                BOOL blVisible = TRUE;
                if (::SendMessage (hWndChild, MWM_GET_WND_RECORDED_VISIBLE_STATE, (WPARAM)&blVisible, _VOL_MSG_ACK) == _VOL_MSG_ACK)  // 避免将"可视"属性设置为假的组件显示出来
                    ::ShowWindow (hWndChild, ((blVisible && nGroupNumber == nChildTabIndex) ? SW_SHOWNA : SW_HIDE));
                else
                    ::ShowWindow (hWndChild, (nGroupNumber == nChildTabIndex ? SW_SHOWNA : SW_HIDE));

                ::UpdateWindow (hWndChild);
            }
        }

        ::InvalidateRect (hTabWnd, NULL, FALSE);
        SetFocusToFisrtFocusableChildControl (hTabWnd);
    }
}

static HWND sFindFirstChildControlFocusable (const HWND hWnd, HWND* phwndTabStop)
{
    ASSERT (phwndTabStop != NULL);

    if (hWnd == NULL || ::IsWindowVisible (hWnd) == FALSE || ::IsWindowEnabled (hWnd) == FALSE)
        return NULL;

    for (HWND hWndChild = ::GetWindow (hWnd, GW_CHILD);
            hWndChild != NULL;
            hWndChild = ::GetWindow (hWndChild, GW_HWNDNEXT))
    {
        if (::IsWindowVisible (hWndChild) && ::IsWindowEnabled (hWndChild))
        {
            const DWORD dwCode = (DWORD)::SendMessage (hWndChild, WM_GETDLGCODE, 0, 0);
            if ((dwCode & (DLGC_WANTALLKEYS | DLGC_WANTARROWS | DLGC_WANTCHARS | DLGC_WANTMESSAGE | DLGC_WANTTAB)) != 0)  // 需要进行键盘输入?
                return hWndChild;

            if (*phwndTabStop == NULL && (GetWindowLong (hWndChild, GWL_STYLE) & WS_TABSTOP) != 0)
                *phwndTabStop = hWndChild;

            const HWND hwndFound = sFindFirstChildControlFocusable (hWndChild, phwndTabStop);
            if (hwndFound != NULL)
                return hwndFound;
        }
    }

    return NULL;
}

void SetFocusToFisrtFocusableChildControl (HWND hWnd)
{
    HWND hwndFocus;

    do
    {
        HWND hwndTabStop = NULL;
        hwndFocus = sFindFirstChildControlFocusable (hWnd, &hwndTabStop);
        if (hwndFocus != NULL)
            break;

        if (hwndTabStop != NULL)
        {
            hwndFocus = hwndTabStop;
            break;
        }

        hwndFocus = ::GetWindow (hWnd, GW_CHILD);
    }
    while (FALSE);

    if (hwndFocus != NULL)
        ::SetFocus (hwndFocus);
}

BOOL IsVolControlVisible (HWND hControlWnd)
{
    if (hControlWnd == NULL)
        return FALSE;

    BOOL blVisible = FALSE;
    if (::SendMessage (hControlWnd, MWM_GET_WND_RECORDED_VISIBLE_STATE, (WPARAM)&blVisible, _VOL_MSG_ACK) == _VOL_MSG_ACK)
        return blVisible;

    return ::IsWindowVisible (hControlWnd);
}

void ShowVolControl (HWND hControlWnd, BOOL_P blpVisible)
{
    if (hControlWnd == NULL)
        return;

    // 首先同步记录最新可视状态
    ::SendMessage (hControlWnd, MWM_RECORD_WND_VISIBLE_STATE, (WPARAM)blpVisible, _VOL_MSG_ACK);

    if (blpVisible)  // 显示组件?
    {
        // 避免将位于被隐藏子选择夹中的组件显示出来
        HWND hParent = ::GetParent (hControlWnd);
        while (hParent != NULL)
        {
            INT nChildTabIndex = -1;
            if (::SendMessage (hParent, MWM_GET_CURRENT_CHILD_TAB_INDEX, (WPARAM)&nChildTabIndex, _VOL_MSG_ACK) == _VOL_MSG_ACK &&
                    nChildTabIndex >= 0)  // 为选择夹?
            {
                const INT nGroupNumber = GetVolControlGroupNumber (hControlWnd);
                if (nGroupNumber >= 0 && nGroupNumber != nChildTabIndex)  // 不位于当前子夹中?
                    blpVisible = FALSE;

                break;
            }

            hParent = ::GetParent (hParent);
        }
    }

    ::ShowWindow (hControlWnd, (blpVisible ? SW_SHOW : SW_HIDE));
}

void vol_print (FILE* stream, INT_P npNumTexts, BOOL_P blpNewLine, ...)
{
    if (stream == NULL || npNumTexts <= 0)
        return;

    va_list argList;
    va_start (argList, blpNewLine);

    CVolString strOutput;
    for (INT_P npIndex = 0; npIndex < npNumTexts; npIndex++)
    {
        if (blpNewLine == FALSE && strOutput.IsEmpty () == FALSE)
            strOutput.AddText (_T (", "));

        strOutput.AddText (va_arg (argList, const TCHAR*));

        if (blpNewLine)
            strOutput.AddText (_T ("\r\n"));
    }

    va_end (argList);

    _ftprintf (stream, _T ("%s"), strOutput.GetText ());
}
