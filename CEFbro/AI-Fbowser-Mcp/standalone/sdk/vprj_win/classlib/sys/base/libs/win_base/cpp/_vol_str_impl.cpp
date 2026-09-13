
// Copyright (C) Recursion Company. All rights reserved.

#include "../include/_vol_str_macro.h"

BOOL_P EndOf (const _MYS_TCHAR* szTest, const _MYS_TCHAR* szEndOf)
{
    ASSERT_R_STR (szTest);
    ASSERT_R_STR (szEndOf);

    const INT_P npTestStrLen = _MYS_STRLEN (szTest);
    const INT_P npEndStrLen = _MYS_STRLEN (szEndOf);
    return (npEndStrLen == 0 || (npTestStrLen >= npEndStrLen && _MYS_STRCMP (szTest + npTestStrLen - npEndStrLen, szEndOf) == 0));
}

BOOL_P IEndOf (const _MYS_TCHAR* szTest, const _MYS_TCHAR* szEndOf)
{
    ASSERT_R_STR (szTest);
    ASSERT_R_STR (szEndOf);

    const INT_P npTestStrLen = _MYS_STRLEN (szTest);
    const INT_P npEndStrLen = _MYS_STRLEN (szEndOf);
    return (npEndStrLen == 0 || (npTestStrLen >= npEndStrLen && _MYS_STRICMP (szTest + npTestStrLen - npEndStrLen, szEndOf) == 0));
}

const _MYS_TCHAR* SkipSpaces (const _MYS_TCHAR* ps)
{
    ASSERT_R_STR (ps);

    while (*ps != '\0')
    {
        if (IS_SPACE_CHAR_NOT_CHECK_ZERO (*ps) == FALSE)
            break;

        ps++;
    }

    return ps;
}

const _MYS_TCHAR* SkipSpaces (const _MYS_TCHAR* ps, const _MYS_TCHAR* psEndMark)
{
    ASSERT_R_STR (ps);
    ASSERT (psEndMark != NULL);

    while (ps < psEndMark)
    {
        if (IS_SPACE_CHAR_NOT_CHECK_ZERO (*ps) == FALSE)
            break;

        ps++;
    }

    return ps;
}

const _MYS_TCHAR* RSkipSpaces (const _MYS_TCHAR* ps, const _MYS_TCHAR* psBegin)
{
    ASSERT_R_STR (ps);
    ASSERT (psBegin != NULL);

    while (ps >= psBegin)
    {
        if (IS_SPACE_CHAR_NOT_CHECK_ZERO (*ps) == FALSE)
            break;

        ps--;
    }

    return ps;
}

void ConvertToLowerText (_MYS_TCHAR* ps)
{
    ASSERT_R_STR (ps);

    while (TRUE)
    {
        const UINT_P upChar = (UINT_P)*ps;
        if (upChar == '\0')
            break;

        if (IS_UPPER_CASE (upChar))
            *ps = (_MYS_TCHAR)(upChar - (UINT_P)'A' + (UINT_P)'a');

        ps++;
    }
}

void ConvertToUpperText (_MYS_TCHAR* ps)
{
    ASSERT_R_STR (ps);

    while (TRUE)
    {
        const UINT_P upChar = (UINT_P)*ps;
        if (upChar == '\0')
            break;

        if (IS_LOWER_CASE (upChar))
            *ps = (_MYS_TCHAR)(upChar - (UINT_P)'a' + (UINT_P)'A');

        ps++;
    }
}

//----------------------------------------------------------------------------------

const _MYS_TCHAR* N64ToStr (INT64 n64, _MYS_TCHAR* psBuf, const INT_P npBufLength)
{
    ASSERT (npBufLength >= 26);
    ASSERT_RW_ADR (psBuf, npBufLength * sizeof (_MYS_TCHAR));

    if (npBufLength < 26)  // 26为最小需求尺寸(可能能更小,但是无需太精确)
        return _MYS_T ("");

    if (n64 == 0)
    {
        psBuf [0] = '0';
        psBuf [1] = '\0';
        return psBuf;
    }
    
    if (n64 == _VOL_INT64_MIN)  // 此值在下面转换为正数时会失败
        return _MYS_T ("-9223372036854775808");

    //----------------------------------------------------

    _MYS_TCHAR buf [32];
    _MYS_TCHAR* ps = &buf [NUM_ELEMENTS_OF (buf) - 1];
    *ps-- = '\0';

    const BOOL_P blpIsNeg = (n64 < 0);  // 获得是否为负数
    if (blpIsNeg)
        n64 = -n64;  // 将负数转换为正数
    ASSERT (n64 > 0);

    while (n64 > 0)
    {
        ASSERT (ps > buf);
        *ps-- = (n64 % 10) + '0';
        n64 /= 10;
    }

    ASSERT (ps >= buf);
    if (blpIsNeg)
        *ps = '-';
    else
        ps++;

    _MYS_STRCPY (psBuf, ps);
    return psBuf;
}

INT_P HexCharToValue (const _MYS_TCHAR chHexChar)
{
    if (IS_NUMBER_CHAR (chHexChar))
        return (INT_P)(chHexChar - '0');
    
    if (chHexChar >= 'A' && chHexChar <= 'F')
        return (INT_P)(chHexChar - 'A' + 10);

    if (chHexChar >= 'a' && chHexChar <= 'f')
        return (INT_P)(chHexChar - 'a' + 10);
    
    return -1;
}

UINT_P Hex2UP (const _MYS_TCHAR* szHexText)
{
    ASSERT_R_STR (szHexText);

    UINT_P upValue = 0;

    const _MYS_TCHAR* ps = szHexText;
    if (ps [0] == '0' && (ps [1] == 'x' || ps [1] == 'X'))  // 为"0x"十六进制格式?
        ps += 2;

    while (TRUE)
    {
        const UINT_P upChar = (UINT_P)*ps++;

        if (IS_NUMBER_CHAR (upChar))
            upValue = ((upValue << 4) | (upChar - '0'));
        else if (upChar >= 'A' && upChar <= 'F')
            upValue = ((upValue << 4) | (upChar - 'A' + 10));
        else if (upChar >= 'a' && upChar <= 'f')
            upValue = ((upValue << 4) | (upChar - 'a' + 10));
        else
            return upValue;
    }
}

UINT64 Hex2U64 (const _MYS_TCHAR* szHexText)
{
    ASSERT_R_STR (szHexText);

    UINT64 u64Value = 0;

    const _MYS_TCHAR* ps = szHexText;
    if (ps [0] == '0' && (ps [1] == 'x' || ps [1] == 'X'))  // 为"0x"十六进制格式?
        ps += 2;

    while (TRUE)
    {
        const UINT_P upChar = (UINT_P)*ps++;

        if (IS_NUMBER_CHAR (upChar))
            u64Value = ((u64Value << 4) | (upChar - '0'));
        else if (upChar >= 'A' && upChar <= 'F')
            u64Value = ((u64Value << 4) | (upChar - 'A' + 10));
        else if (upChar >= 'a' && upChar <= 'f')
            u64Value = ((u64Value << 4) | (upChar - 'a' + 10));
        else
            return u64Value;
    }
}

void Byte2TwoHexChars (const UINT_P upByte, _MYS_TCHAR* psTwoChars)
{
    ASSERT_RW_ADR (psTwoChars, sizeof (_MYS_TCHAR) * 2);

    const static _MYS_TCHAR cs_hex [] =
    {
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F'
    };
    COMPILE_TIME_ASSERT (NUM_ELEMENTS_OF (cs_hex) == 16);

    psTwoChars [0] = cs_hex [(upByte >> 4) & 0x0F];
    psTwoChars [1] = cs_hex [upByte & 0x0F];
}

INT64 StrToN64 (const _MYS_TCHAR* ps)
{
    ASSERT_R_STR (ps);

    // 跳过空白
    while (*ps != '\0' && (DWORD)*ps <= (DWORD)' ')
        ps++;

    // 跳过空白后遇到了文本结束符?
    if (*ps == '\0')
        return 0;

    // 获取数值符号
    BOOL_P blpNeg;  // 记录是否为负数
    if (*ps == '-')
    {
        blpNeg = TRUE;
        ps++;
    }
    else
    {
        blpNeg = FALSE;

        if (*ps == '+')
            ps++;
    }

    // 用作计算是否溢出时使用
    const UINT64 c_ui64Cutoff = _VOL_UINT64_MAX / (UINT64)10;
    const DWORD c_dwCutlim = (DWORD)(_VOL_UINT64_MAX % (UINT64)10);

    // 用作记录所获得的值
    UINT64 u64Value = 0;

    // 转换每个字符
    DWORD c = (DWORD)*ps;
    while (IS_NUMBER_CHAR (c))  // 为数字?
    {
        c -= '0';

        if (u64Value > c_ui64Cutoff || (u64Value == c_ui64Cutoff && c > c_dwCutlim))  // 检查是否会导致溢出UINT64
            return (blpNeg ? _VOL_INT64_MIN : _VOL_INT64_MAX);  // 如果溢出则直接返回

        // 加入该数值
        u64Value *= (UINT64)10;
        u64Value += (UINT64)c;

        // 去处理下一个数字
        ps++;
        c = *ps;
    }

    if (blpNeg)
        return (/*((INT64)u64Value) < 0 ? _VOL_INT64_MIN : */-((INT64)u64Value));
    else
        return (/*u64Value > _VOL_INT64_MAX ? _VOL_INT64_MAX : */((INT64)u64Value));
}

BOOL_P CheckUnsignInteger (const _MYS_TCHAR* ps)
{
    ASSERT_R_STR (ps);

    const _MYS_TCHAR* psBegin = ps;

    if (*ps == '\0')  // 为空文本?
        return FALSE;

    // 检查内容的有效性
    for (; *ps != '\0'; ps++)
    {
        if (IS_NUMBER_CHAR (*ps) == FALSE)  // 不为数字?
            return FALSE;
    }

    return TRUE;
}

BOOL_P CheckHexInteger (const _MYS_TCHAR* ps)
{
    ASSERT_R_STR (ps);
    
    const _MYS_TCHAR* psBegin = ps;

    if (*ps == '\0')  // 为空文本?
        return FALSE;

    // 检查内容的有效性
    for (; *ps != '\0'; ps++)
    {
        const UINT_P upChar = *ps;

        if (IS_NUMBER_CHAR (upChar) == FALSE &&  // 不为数字?
                (upChar < 'a' || upChar > 'f') &&
                (upChar < 'A' || upChar > 'F'))
        {
            return FALSE;
        }
    }

    return TRUE;
}

BOOL_P CheckInteger (const _MYS_TCHAR* ps)
{
    ASSERT_R_STR (ps);
    
    if (*ps == '+' || *ps == '-')  // 为数值符号?
        ps++;

    return CheckUnsignInteger (ps);
}

BOOL_P Str2IntCheck (const _MYS_TCHAR* ps, INT_P* pnpResult)
{
    ASSERT_R_STR (ps);
    ASSERT_RW_DATA (pnpResult);

    *pnpResult = 0;  // 初始化返回值

    if (ps [0] == '0' && (ps [1] == 'x' || ps [1] == 'X'))  // 为"0x"十六进制格式?
    {
        ps += 2;

        if (CheckHexInteger (ps) == FALSE)
            return FALSE;

        *pnpResult = (INT_P)Hex2UP (ps);
    }
    else
    {
        if (CheckInteger (ps) == FALSE)
            return FALSE;

        *pnpResult = _MYS_TTOI (ps);
    }

    return TRUE;
}

BOOL_P Str2Int64Check (const _MYS_TCHAR* ps, INT64* pn64Result, BOOL_P* pblpIsHexNumber)
{
    ASSERT_R_STR (ps);
    ASSERT_RW_DATA (pn64Result);

    // 初始化返回值
    *pn64Result = 0;
    if (pblpIsHexNumber != NULL)
    {
        ASSERT_RW_DATA (pblpIsHexNumber);
        *pblpIsHexNumber = FALSE;
    }

    if (ps [0] == '0' && (ps [1] == 'x' || ps [1] == 'X'))  // 为"0x"十六进制格式?
    {
        ps += 2;

        if (CheckHexInteger (ps) == FALSE)
            return FALSE;

        *pn64Result = (INT64)Hex2U64 (ps);

        if (pblpIsHexNumber != NULL)
            *pblpIsHexNumber = TRUE;
    }
    else
    {
        if (CheckInteger (ps) == FALSE)
            return FALSE;

        *pn64Result = StrToN64 (ps);
    }

    return TRUE;
}

BOOL_P Str2DoubleCheck (const _MYS_TCHAR* ps, DOUBLE* pdbResult)
{
    ASSERT_R_STR (ps);
    ASSERT_RW_DATA (pdbResult);
    
    *pdbResult = 0;  // 初始化返回值

    const _MYS_TCHAR* psBegin = ps;

    if (*ps == '+' || *ps == '-')  // 为数值符号?
        ps++;

    if (IS_NUMBER_CHAR (*ps) == FALSE)  // 不为数字?
        return FALSE;

    // 检查内容的有效性
    BOOL_P blpDotFound = FALSE;  // 记录是否已经遇到小数点
    for (; *ps != '\0'; ps++)
    {
        const _MYS_TCHAR ch = *ps;

        if (ch == '.')  // 为小数点?
        {
            if (blpDotFound == FALSE)  // 尚未遇到过小数点?
            {
                blpDotFound = TRUE;  // 标记已经遇到了小数点
                continue;
            }
            // 遇到了多个小数点
        }
        else if (IS_NUMBER_CHAR (ch))  // 为数字?
        {
            continue;
        }
        else if (ch == 'e' || ch == 'E')  // 科学计数法?
        {
            if (CheckInteger (ps + 1) == FALSE)  // 指数部分不为规范的整数格式?
                return FALSE;
            else
                break;
        }

        return FALSE;
    }

    *pdbResult = _MYS_TTOF (psBegin);
    return TRUE;
}

BOOL_P Str2FloatCheck (const _MYS_TCHAR* ps, FLOAT* pfResult)
{
    ASSERT_R_STR (ps);
    ASSERT_RW_DATA (pfResult);

    DOUBLE dbResult;
    if (Str2DoubleCheck (ps, &dbResult) == FALSE)
    {
        *pfResult = 0;
        return FALSE;
    }

    *pfResult = (FLOAT)dbResult;
    return TRUE;
}

const _MYS_TCHAR* FindString (const _MYS_TCHAR* psText, INT_P npTextLength, const _MYS_TCHAR* psFindText, INT_P npFindTextLength,
        const BOOL_P blpCaseInsensitive, const BOOL_P blpReverseFind)
{
    ASSERT_R_STR2_NEG1 (psText, npTextLength);
    ASSERT_R_STR2_NEG1 (psFindText, npFindTextLength);

    if (npTextLength < 0)
        npTextLength = _MYS_STRLEN (psText);
    if (npFindTextLength < 0)
        npFindTextLength = _MYS_STRLEN (psFindText);

    if (npFindTextLength <= 0)
        return NULL;

    // 获得实际搜寻文本最大处理长度
    const INT_P npLength = npTextLength - npFindTextLength + 1;
    if (npLength <= 0)
        return NULL;

    // 获得被搜寻文本内容的尾部指针
    const _MYS_TCHAR* psTextEnd = psText + npTextLength;

    if (blpReverseFind == FALSE)  // 正向查找?
    {
        const _MYS_TCHAR* psCurrent = psText;

        for (INT_P npIndex1 = 0; npIndex1 < npLength; npIndex1++, psCurrent++)
        {
            const _MYS_TCHAR* ps1 = psCurrent;
            const _MYS_TCHAR* ps2 = psFindText;

            for (INT_P npIndex2 = 0; ; npIndex2++, ps1++, ps2++)
            {
                if (npIndex2 == npFindTextLength)  // 字母全部匹配?
                    return psCurrent;

                ASSERT (ps1 >= psText && ps1 < psTextEnd &&
                        ps2 >= psFindText && ps2 < psFindText + npFindTextLength);

                if (blpCaseInsensitive ?  // 字母大小写无关?
                        (TO_UPPER_CASE (*ps1) != TO_UPPER_CASE (*ps2)) :
                        *ps1 != *ps2)
                {
                    break;
                }
            }
        }
    }
    else  // 逆向查找
    {
        const _MYS_TCHAR* psCurrent = psTextEnd - 1;

        for (INT_P npIndex1 = 0; npIndex1 < npLength; npIndex1++, psCurrent--)
        {
            const _MYS_TCHAR* ps1 = psCurrent;
            const _MYS_TCHAR* ps2 = psFindText + npFindTextLength - 1;

            for (INT_P npIndex2 = 0; ; npIndex2++, ps1--, ps2--)
            {
                if (npIndex2 == npFindTextLength)  // 字母全部匹配?
                    return ps1 + 1;

                ASSERT (ps1 >= psText && ps1 < psTextEnd &&
                        ps2 >= psFindText && ps2 < psFindText + npFindTextLength);

                if (blpCaseInsensitive ?  // 字母大小写无关?
                        (TO_UPPER_CASE (*ps1) != TO_UPPER_CASE (*ps2)) :
                        *ps1 != *ps2)
                {
                    break;
                }
            }
        }
    }

    return NULL;
}


//----------------------------------------------------------------------------------

#ifdef _MY_WSTRING_IMPL
_MY_STRING::_MY_STRING (const CU8String& str) : _MY_STRING ()
#else
_MY_STRING::_MY_STRING (const CWString& str) : _MY_STRING ()
#endif
{
    AddText (str.GetText ());
}

void _MY_STRING::_CopySelfFrom (const _MY_STRING& objCopyFrom)
{
    SetText (objCopyFrom);
}

BOOL _MY_STRING::_IsSelfEqual (const _MY_STRING& objCompare) const
{
    return (_MYS_STRCMP (GetText (), objCompare.GetText ()) == 0);
}

CVolMem& _MY_STRING::CheckConvertConstText ()
{
    if (m_szConstText != NULL)  // 所记录的是常量文本?
    {
        // 转换为非常量文本
        m_mem.CopyFrom (m_szConstText, (_MYS_STRLEN (m_szConstText) + 1) * sizeof (_MYS_TCHAR));
        m_szConstText = NULL;
    }

    return m_mem;
}

void _MY_STRING::LoadFromStream (CVolBaseInputStream& stream)
{
    BaseClass::LoadFromStream (stream);

    Empty ();
    m_mem.LoadFromStream (stream);
}

void _MY_STRING::SaveIntoStream (CVolBaseOutputStream& stream)
{
    BaseClass::SaveIntoStream (stream);

    if (m_szConstText != NULL)  // 为常量文本?
        _MY_STRING (*this).CheckConvertConstText ().SaveIntoStream (stream);
    else
        m_mem.SaveIntoStream (stream);
}

_MY_STRING _MY_STRING::sGetRepeatText (const _MYS_TCHAR* szText, const INT_P npNumRepeat)
{
    _MY_STRING str;

    for (INT_P npIndex = 0; npIndex < npNumRepeat; npIndex++)
        str.AddText (szText);

    return str;
}

const _MYS_TCHAR* _MY_STRING::GetText () const
{
    return (m_szConstText != NULL ? m_szConstText :
            m_mem.IsEmpty () ? _MYS_T ("") :
            (const _MYS_TCHAR*)m_mem.GetPtr ());
}

INT_P _MY_STRING::GetLength () const
{
    if (m_szConstText != NULL)
        return _MYS_STRLEN (m_szConstText);

    const INT_P npSize = m_mem.GetSize ();
    return (npSize == 0 ? 0 : npSize / sizeof (_MYS_TCHAR) - 1);
}

void _MY_STRING::SetConstText (const _MYS_TCHAR* szConstText)
{
    ASSERT_R_STR_OR_NULL (szConstText);

    m_szConstText = szConstText;
    m_mem.Free ();
}

void _MY_STRING::AddFloatText (const FLOAT flt)
{
    if (IsFloatEqualZero (flt))
    {
        AddChar ('0');
    }
    else
    {
        _MYS_TCHAR buf [128];
        _MYS_SPRINTF (buf, _MYS_T ("%.8G"), (DOUBLE)flt);
        AddText (buf);
    }
}

void _MY_STRING::AddDoubleText (const DOUBLE db)
{
    _MYS_TCHAR buf [128];
    if (IsDoubleEqualZero (db))
    {
        buf [0] = '0';
        buf [1] = '\0';
    }
    else
    {
        _MYS_SPRINTF (buf, _MYS_T ("%.15G"), db);
    }

    AddText (buf);
}

void _MY_STRING::AddIntText (const INT n)
{
    _MYS_TCHAR buf [64];
    _MYS_SPRINTF (buf, _MYS_T ("%d"), n);
    AddText (buf);
}

void _MY_STRING::AddDWordText (const DWORD dw)
{
    _MYS_TCHAR buf [64];
    _MYS_SPRINTF (buf, _MYS_T ("%u"), dw);
    AddText (buf);
}

void _MY_STRING::AddInt64Text (const INT64 n64)
{
    _MYS_TCHAR buf [64];
    AddText (N64ToStr (n64, buf, NUM_ELEMENTS_OF (buf)));
}

void _MY_STRING::AddUInt64Text (const UINT64 u64)
{
    _MYS_TCHAR buf [64];
    _MYS_SPRINTF (buf, _MYS_T ("%I64u"), u64);
    AddText (buf);
}

void _MY_STRING::AddIntPText (const INT_P np)
{
    _MYS_TCHAR buf [64];
#ifdef _PF_64_BITS  // 64位目标平台?
    _MYS_SPRINTF (buf, _MYS_T ("%I64d"), np);
#else
    _MYS_SPRINTF (buf, _MYS_T ("%d"), np);
#endif
    AddText (buf);
}

void _MY_STRING::AddUIntPText (const UINT_P up)
{
    _MYS_TCHAR buf [64];
#ifdef _PF_64_BITS  // 64位目标平台?
    _MYS_SPRINTF (buf, _MYS_T ("%I64u"), up);
#else
    _MYS_SPRINTF (buf, _MYS_T ("%u"), up);
#endif
    AddText (buf);
}

void _MY_STRING::SetTextWithoutControlChars (const _MYS_TCHAR* ps, INT_P npLen, const BOOL_P blpAllowLFChar)
{
    ASSERT (npLen >= 0);
    ASSERT_R_STR2 (ps, npLen);

    Empty ();

    if (npLen <= 0)  // 文本为空?
        return;

    _MYS_TCHAR* psBegin = (_MYS_TCHAR*)m_mem.Alloc ((npLen + 1) * sizeof (_MYS_TCHAR));  // 分配足够尺寸的空间
    _MYS_TCHAR* psDest = psBegin;  // 获得目的文本指针

    for (; npLen > 0; npLen--, ps++)
    {
        const UINT_P upChar = (UINT_P)*ps;

        if (upChar == '\t')
        {
            *psDest++ = ' ';  // 转换为空格
        }
        else if (upChar >= (UINT_P)' ' ||  // 不为控制类字符?
                (upChar == '\n' && blpAllowLFChar))  // 为换行符且允许包括换行符?
        {
            *psDest++ = (_MYS_TCHAR)upChar;
        }
    }

    if (psDest == psBegin)  // 未加入任何字符?
    {
        m_mem.Empty ();
    }
    else
    {
        ASSERT (m_mem.IsInside (psDest, sizeof (_MYS_TCHAR)));
        *psDest++ = '\0';  // 写入结束字符

        m_mem.Realloc ((psDest - psBegin) * sizeof (_MYS_TCHAR));  // 去除多余的已分配空间
    }
}

void _MY_STRING::SetTextReplaceLF2CRLF (const _MYS_TCHAR* ps, const INT_P npLen)
{
    ASSERT (npLen >= 0);
    ASSERT_R_STR2 (ps, npLen);

    Empty ();

    if (npLen <= 0)  // 文本为空?
        return;

    _MYS_TCHAR* psBegin = (_MYS_TCHAR*)m_mem.Alloc ((npLen * 2 + 1) * sizeof (_MYS_TCHAR));  // 分配足够尺寸的空间
    _MYS_TCHAR* psDest = psBegin;  // 获得目的文本指针

    for (INT_P npIndex = 0; npIndex < npLen; npIndex++)
    {
        if (*ps == '\n' && (npIndex == 0 || *(ps - 1) != '\r'))  // 为单独的换行符?
            *psDest++ = '\r';

        *psDest++ = *ps++;
    }

    ASSERT (m_mem.IsInside (psDest, sizeof (_MYS_TCHAR)));  // 所分配空间必定足够
    *psDest++ = '\0';  // 写入结束字符

    m_mem.Realloc ((psDest - psBegin) * sizeof (_MYS_TCHAR));  // 去除多余的已分配空间
}

void _MY_STRING::SetTextReplaceCRLF2LF (const _MYS_TCHAR* ps, const INT_P npLen)
{
    ASSERT (npLen >= 0);
    ASSERT_R_STR2 (ps, npLen);

    Empty ();

    if (npLen <= 0)  // 文本为空?
        return;

    _MYS_TCHAR* psBegin = (_MYS_TCHAR*)m_mem.Alloc ((npLen + 1) * sizeof (_MYS_TCHAR));  // 分配足够尺寸的空间
    _MYS_TCHAR* psDest = psBegin;  // 获得目的文本指针

    for (INT_P npIndex = 0; npIndex < npLen; npIndex++, ps++)
    {
        if (*ps == '\r' && (npIndex + 1 < npLen || ps [1] == '\n'))  // 为回车换行连续两个字符?
            continue;  // 跳过回车字符

        *psDest++ = *ps;
    }

    ASSERT (m_mem.IsInside (psDest, sizeof (_MYS_TCHAR)));  // 所分配空间必定足够
    *psDest++ = '\0';  // 写入结束字符

    m_mem.Realloc ((psDest - psBegin) * sizeof (_MYS_TCHAR));  // 去除多余的已分配空间
}

void _MY_STRING::ReplaceAllControlCharsToSpace ()
{
    if (IsEmpty ())
        return;

    _MYS_TCHAR* ps = (_MYS_TCHAR*)CheckConvertConstText ().GetPtr ();

    while (TRUE)
    {
        const UINT_P upChar = (UINT_P)*ps;

        if (upChar < (UINT_P)' ')
        {
            if (upChar == '\0')
                break;

            *ps = ' ';
        }

        ps++;
    }
}

void _MY_STRING::MReplaceText (INT_P npBeginIndex, INT_P npReplaceLen, const _MYS_TCHAR* szReplaceText)
{
    ASSERT (npBeginIndex >= 0 && npReplaceLen >= 0 && npBeginIndex + npReplaceLen <= GetLength ());
    ASSERT_R_STR (szReplaceText);

    const INT_P npTextLength = GetLength ();
    if (npBeginIndex > npTextLength)
        return;

    CheckConvertConstText ();

    INT_P npEndIndex = npBeginIndex + npReplaceLen;

    if (npBeginIndex < 0)
        npBeginIndex = 0;

    if (npEndIndex > npTextLength)
        npEndIndex = npTextLength;

    npReplaceLen = npEndIndex - npBeginIndex;
    if (npReplaceLen < 0)
        npReplaceLen = 0;

    m_mem.Replace (npBeginIndex * sizeof (_MYS_TCHAR), npReplaceLen * sizeof (_MYS_TCHAR),
            szReplaceText, _MYS_STRLEN (szReplaceText) * sizeof (_MYS_TCHAR));
}

void _MY_STRING::ReplaceSubText (const _MYS_TCHAR* szFindText, const _MYS_TCHAR* szReplaceText, INT_P npBeginIndex,
        INT_P npReplaceTimes, const BOOL_P blpCaseInsensitive)
{
    ASSERT (npBeginIndex >= 0 && npBeginIndex <= GetLength () && npReplaceTimes >= -1);
    ASSERT_R_STR (szFindText);
    ASSERT_R_STR (szReplaceText);

    if (npBeginIndex < 0)
        npBeginIndex = 0;

    INT_P npBeSearchedTextLen = GetLength ();
    const INT_P npSubTextLen = _MYS_STRLEN (szFindText);
    const INT_P npSubTextDataSize = npSubTextLen * sizeof (_MYS_TCHAR);
    const INT_P npReplaceTextDataSize = _MYS_STRLEN (szReplaceText) * sizeof (_MYS_TCHAR);

    if (npBeSearchedTextLen < npSubTextLen || npBeginIndex >= npBeSearchedTextLen || npSubTextLen == 0 || npReplaceTimes == 0)
        return;

    //--------------------------------------------------------------------------

    CheckConvertConstText ();

    const _MYS_TCHAR* ps = GetText () + npBeginIndex;
    npBeSearchedTextLen -= npBeginIndex;

    while (npBeSearchedTextLen >= npSubTextLen)
    {
        ASSERT ((const BYTE*)ps >= m_mem.GetPtr () &&
                (const BYTE*)(ps + npBeSearchedTextLen) <= m_mem.GetEndPtr ());

        if ((blpCaseInsensitive ?
                _MYS_STRNICMP (ps, szFindText, npSubTextLen) :
                _MYS_STRNCMP (ps, szFindText, npSubTextLen)) == 0)
        {
            const INT_P npOffset = (const BYTE*)ps - m_mem.GetPtr ();
            ASSERT (npOffset >= 0 && npOffset + npSubTextDataSize <= m_mem.GetSize ());
            m_mem.Replace (npOffset, npSubTextDataSize, szReplaceText, npReplaceTextDataSize);

            if (npReplaceTimes > 0)  // 不为替换无限次?
            {
                npReplaceTimes--;
                if (npReplaceTimes == 0)
                    break;
            }

            ps = (const _MYS_TCHAR*)(m_mem.GetPtr () + npOffset + npReplaceTextDataSize);
            npBeSearchedTextLen -= npSubTextLen;
        }
        else
        {
            ps++;
            npBeSearchedTextLen--;
        }
    }
}

BOOL_P _MY_STRING::Replace (const _MYS_TCHAR* szFindText, const _MYS_TCHAR* szReplaceText)
{
    ASSERT (IsEmptyStr (szFindText) == FALSE);
    ASSERT_R_STR (szFindText);
    ASSERT_R_STR (szReplaceText);

    if (IsEmpty ())  // 本对象文本内容为空?
        return FALSE;

    // 获得待寻找文本的数据尺寸
    const INT_P npFindTextDataSize = _MYS_STRLEN (szFindText) * sizeof (_MYS_TCHAR);
    if (npFindTextDataSize == 0)
        return FALSE;
    // 获得待替换文本的数据尺寸
    const INT_P npReplaceTextDataSize = _MYS_STRLEN (szReplaceText) * sizeof (_MYS_TCHAR);

    INT_P npCurrentFindOffset = 0;  // 用作记录当前搜寻偏移字节位置
    BOOL_P blpReplaced = FALSE;  // 用作记录是否产生了实际替换

    CheckConvertConstText ();

    while (TRUE)
    {
        // 寻找待寻找文本的位置
        const BYTE* pbBegin = m_mem.GetPtr ();
        ASSERT (m_mem.IsOffsetInside (npCurrentFindOffset, sizeof (_MYS_TCHAR)));
        const _MYS_TCHAR* psFound = _MYS_STRSTR ((const _MYS_TCHAR*)(pbBegin + npCurrentFindOffset), szFindText);
        if (psFound == NULL)  // 未找到?
            break;

        npCurrentFindOffset = (const BYTE*)psFound - pbBegin;  // 计算所找到文本的偏移字节位置
        m_mem.Replace (npCurrentFindOffset, npFindTextDataSize, szReplaceText, npReplaceTextDataSize);  // 进行替换
        npCurrentFindOffset += npReplaceTextDataSize;  // 到下一寻找位置
        blpReplaced = TRUE;  // 记录产生了实际替换
    }

    return blpReplaced;
}

BOOL_P _MY_STRING::Replace (const INT_P npBeginCharIndex, const _MYS_TCHAR chFind, const _MYS_TCHAR chReplace)
{
    ASSERT (npBeginCharIndex >= 0 && npBeginCharIndex <= GetLength () &&
            chFind != '\0' && chReplace != '\0');

    if (chFind == chReplace)
        return FALSE;

    _MYS_TCHAR* ps = (_MYS_TCHAR*)CheckConvertConstText ().GetPtr () + npBeginCharIndex;
    const INT_P npLength = GetLength ();

    BOOL_P blpReplaced = FALSE;  // 用作记录是否产生了实际替换

    for (INT_P i = npBeginCharIndex; i < npLength; i++, ps++)
    {
        if (*ps == chFind)
        {
            *ps = chReplace;
            blpReplaced = TRUE;  // 记录产生了实际替换
        }
    }

    return blpReplaced;
}

void _MY_STRING::SetLength (const INT_P npNewLength)
{
    ASSERT (npNewLength >= 0);

    const INT_P npOldLength = GetLength ();
    if (npNewLength == npOldLength)  // 长度未发生改变?
        return;

    if (npNewLength <= 0)  // 设置新长度为0?
    {
        Empty ();
    }
    else
    {
        CheckConvertConstText ();

        // 重新分配对应尺寸的空间
        _MYS_TCHAR* psNew = (_MYS_TCHAR*)m_mem.Realloc (sizeof (_MYS_TCHAR) * (npNewLength + 1));

        // 如果大于原有文本长度,则在尾部补充对应数目的空白字符.
        for (INT_P npIndex = npOldLength; npIndex < npNewLength; npIndex++)
            psNew [npIndex] = ' ';

        psNew [npNewLength] = '\0';  // 写入结束'\0'字符
    }
}

_MYS_TCHAR* _MY_STRING::InitWithChars (const INT_P npNumChars, const _MYS_TCHAR ch)
{
    ASSERT (npNumChars >= 0 && ch != '\0');

    Empty ();

    if (npNumChars > 0)
    {
        _MYS_TCHAR* ps = (_MYS_TCHAR*)m_mem.Alloc ((npNumChars + 1) * sizeof (_MYS_TCHAR));

        for (INT_P np = 0; np < npNumChars; np++)
            *ps++ = ch;

        *ps = '\0';
        ASSERT (m_mem.IsAtEnd (ps + 1));

        return (_MYS_TCHAR*)m_mem.GetPtr ();
    }

    return _MYS_T ("");
}

INT_P _MY_STRING::RemoveChars (const INT_P npBeginIndex, INT_P npNumChars)
{
    ASSERT (npBeginIndex >= 0 && npBeginIndex <= GetLength () && npNumChars >= 0);

    const INT_P npOldLength = GetLength ();
    if (npBeginIndex + npNumChars > npOldLength)
        npNumChars = npOldLength - npBeginIndex;

    if (npNumChars > 0)
    {
        CheckConvertConstText ().Remove (npBeginIndex * sizeof (_MYS_TCHAR), npNumChars * sizeof (_MYS_TCHAR));
        return npNumChars;
    }

    return 0;
}

const _MY_STRING& _MY_STRING::operator= (const _MYS_TCHAR ch)
{
    Empty ();

    if (ch != '\0')
    {
        m_mem._MYS_MEM_ADD_CHAR (ch);
        m_mem._MYS_MEM_ADD_CHAR ('\0');
    }

    return *this;
}

const _MY_STRING& _MY_STRING::operator= (const _MYS_TCHAR* ps)
{
    MCHECK_STR_POINTER (ps)

    Empty ();

    if (IsEmptyStr (ps) == FALSE)
        m_mem.AddString (ps);

    return *this;
}

const _MY_STRING& _MY_STRING::operator+= (const _MY_STRING& string)
{
    AddText (string.GetText ());
    return *this;
}

const _MY_STRING& _MY_STRING::operator+= (const _MYS_TCHAR* ps)
{
    MCHECK_STR_POINTER (ps)
    ASSERT_R_STR (ps);

    AddText (ps);
    return *this;
}

void _MY_STRING::InsertChar (const INT_P npIndex, const _MYS_TCHAR ch)
{
    ASSERT (npIndex >= 0 && npIndex <= GetLength ());

    if (ch == '\0')
        return;

    if (IsEmpty ())
    {
        Empty ();
        m_mem._MYS_MEM_ADD_CHAR (ch);
        m_mem._MYS_MEM_ADD_CHAR ('\0');
    }
    else
    {
        CheckConvertConstText ().Insert (npIndex * sizeof (_MYS_TCHAR), &ch, sizeof (ch));
    }
}

void _MY_STRING::AddChar (const _MYS_TCHAR ch)
{
    if (ch == '\0')
        return;

    CheckConvertConstText ()._MYS_MEM_REMOVE_END_ZERO_CHAR ();

    _MYS_TCHAR acBuf [2];
    acBuf [0] = ch;
    acBuf [1] = '\0';
    m_mem.Append (acBuf, sizeof (acBuf));
}

void _MY_STRING::AddChar (const _MYS_TCHAR ch, const INT_P npCount)
{
    if (ch == '\0' || npCount <= 0)
        return;

    CheckConvertConstText ()._MYS_MEM_REMOVE_END_ZERO_CHAR ();

    const INT_P npDataSize = m_mem.GetSize ();
    _MYS_TCHAR* ps = (_MYS_TCHAR*)((BYTE*)m_mem.Realloc (npDataSize + (npCount + 1) * sizeof (_MYS_TCHAR)) + npDataSize);

    for (INT_P np = 0; np < npCount; np++)
        *ps++ = ch;

    *ps = '\0';
    ASSERT (m_mem.IsAtEnd (ps + 1));
}

void _MY_STRING::AddText (const _MYS_TCHAR* ps)
{
    ASSERT_R_STR_OR_NULL (ps);

    if (IsEmptyStr (ps) == FALSE)
    {
        CheckConvertConstText ()._MYS_MEM_REMOVE_END_ZERO_CHAR ();
        m_mem.Append (ps, (_MYS_STRLEN (ps) + 1) * sizeof (_MYS_TCHAR));
    }
}

void _MY_STRING::AddText (const _MYS_TCHAR* ps, const INT_P npLen)
{
    if (npLen > 0)
    {
        ASSERT_R_STR2 (ps, npLen);

        CheckConvertConstText ()._MYS_MEM_REMOVE_END_ZERO_CHAR ();
        m_mem.Append (ps, npLen * sizeof (_MYS_TCHAR));
        m_mem._MYS_MEM_ADD_CHAR ('\0');
    }
}

void _MY_STRING::CheckAddText (const _MYS_TCHAR* ps, INT_P npLen)
{
    ASSERT_R_STR2 (ps, npLen);

    for (INT_P npIndex = 0; npIndex < npLen; npIndex++)
    {
        if (ps [npIndex] == '\0')
        {
            npLen = npIndex;
            break;
        }
    }

    if (npLen > 0)
    {
        CheckConvertConstText ()._MYS_MEM_REMOVE_END_ZERO_CHAR ();

        m_mem.Append (ps, npLen * sizeof (_MYS_TCHAR));
        m_mem._MYS_MEM_ADD_CHAR ('\0');
    }
}

void _MY_STRING::AddMutilLineTextWithLeaderSpaces (const _MYS_TCHAR* szMutilLineText, const INT_P npNumLeaderSpaces)
{
    ASSERT (npNumLeaderSpaces >= 0);
    ASSERT_R_STR (szMutilLineText);

    if (npNumLeaderSpaces <= 0)  // 不需要加入前缀空白?
    {
        AddText (szMutilLineText);
        return;
    }

    //------------------------------------------------------------------------------------

    CheckConvertConstText ()._MYS_MEM_REMOVE_END_ZERO_CHAR ();

    const _MYS_TCHAR* psLineBegin = szMutilLineText;
    const _MYS_TCHAR* ps = psLineBegin;

    while (TRUE)
    {
        const _MYS_TCHAR ch = *ps;

        if (ch == '\0' || ch == '\r' || ch == '\n')  // 到了行尾?
        {
            // 记录当前行
            if (ps > psLineBegin)  // 当前行文本不为空?
            {
                if (npNumLeaderSpaces > 0)  // 加入对应数目的空格字符
                {
                    _MYS_TCHAR* ps2 = (_MYS_TCHAR*)m_mem.AddSpace (npNumLeaderSpaces * sizeof (_MYS_TCHAR), FALSE);
                    for (INT_P npIndex = 0; npIndex < npNumLeaderSpaces; npIndex++)
                        *ps2++ = ' ';
                }
                else  // 删除对应数目的空格字符
                {
                    for (INT_P npIndex = 0; npIndex > npNumLeaderSpaces && psLineBegin < ps && IS_VISIBLE_SPACE_CHAR (*psLineBegin); npIndex--)
                        psLineBegin++;
                }

                m_mem.Append (psLineBegin, (ps - psLineBegin) * sizeof (_MYS_TCHAR));  // 加入本行文本
            }

            if (ch == '\0')
            {
                m_mem._MYS_MEM_ADD_CHAR ('\0');  // 加入结束零字符
                break;
            }

            // 加入回车换行符
            m_mem._MYS_MEM_ADD_CHAR ('\r');
            m_mem._MYS_MEM_ADD_CHAR ('\n');

            // 跳过换行符
            ps++;
            if (ch == '\r' && *ps == '\n')
                ps++;

            psLineBegin = ps;  // 重置行首位置
        }
        else
        {
            ps++;
        }
    }
}

void _MY_STRING::AddLowerText (const _MYS_TCHAR* ps)
{
    const INT_P npOldLength = GetLength ();
    AddText (ps);
    
    ConvertToLowerText ((_MYS_TCHAR*)GetText () + npOldLength);
}

void _MY_STRING::AddLowerText (const _MYS_TCHAR* ps, const INT_P npLen)
{
    const INT_P npOldLength = GetLength ();
    AddText (ps, npLen);
    
    ConvertToLowerText ((_MYS_TCHAR*)GetText () + npOldLength);
}

void _MY_STRING::AddUpperText (const _MYS_TCHAR* ps)
{
    const INT_P npOldLength = GetLength ();
    AddText (ps);
    
    ConvertToUpperText ((_MYS_TCHAR*)GetText () + npOldLength);
}

void _MY_STRING::AddUpperText (const _MYS_TCHAR* ps, const INT_P npLen)
{
    const INT_P npOldLength = GetLength ();
    AddText (ps, npLen);
    
    ConvertToUpperText ((_MYS_TCHAR*)GetText () + npOldLength);
}

void _MY_STRING::InsertText (const INT_P npIndex, const _MYS_TCHAR* ps, const INT_P npLen)
{
    ASSERT (npIndex >= 0 && npIndex <= GetLength () && npLen >= 0);

    if (npLen > 0)
    {
        ASSERT_R_STR2 (ps, npLen);

        if (IsEmpty ())
            AddText (ps, npLen);
        else
            CheckConvertConstText ().Insert (npIndex * sizeof (_MYS_TCHAR), ps, npLen * sizeof (_MYS_TCHAR));
    }
}

void _MY_STRING::SetText (const _MYS_TCHAR* ps)
{
    ASSERT_R_STR_OR_NULL (ps);

    if (ps != GetText ())
    {
        Empty ();

        if (IsEmptyStr (ps) == FALSE)
            m_mem.AddString (ps);
    }
}

void _MY_STRING::SetText (const _MYS_TCHAR* ps, const INT_P npLen)
{
    ASSERT_R_STR2 (ps, npLen);

    Empty ();

    if (npLen > 0)
    {
        m_mem.Append (ps, npLen * sizeof (_MYS_TCHAR));
        m_mem._MYS_MEM_ADD_CHAR ('\0');
    }
}

void _MY_STRING::CheckSetText (const _MYS_TCHAR* ps, INT_P npLen)
{
    ASSERT_R_STR2 (ps, npLen);

    Empty ();

    for (INT_P npIndex = 0; npIndex < npLen; npIndex++)
    {
        if (ps [npIndex] == '\0')
        {
            npLen = npIndex;
            break;
        }
    }

    if (npLen > 0)
    {
        m_mem.Append (ps, npLen * sizeof (_MYS_TCHAR));
        m_mem._MYS_MEM_ADD_CHAR ('\0');
    }
}

void _MY_STRING::SetText (const _MYS_OTHER_CHAR* ps, const INT_P npLen)
{
    ASSERT_R_STR2_NEG1 (ps, npLen);

    Empty ();

#ifdef _MY_WSTRING_IMPL
    if (IsEmptyStr (::Utf8ToWStr (ps, npLen, m_mem, NULL, NULL, TRUE)))
        Empty ();
#else
    if (IsEmptyStr (::WStrToUtf8 (ps, npLen, m_mem, NULL, NULL, TRUE)))
        Empty ();
#endif
}

_MY_STRING& _MY_STRING::ReverseSetText (const _MYS_TCHAR* ps, INT_P npLen)
{
    ASSERT (npLen >= 0);

    Empty ();

    if (npLen > 0)
    {
        ASSERT_R_STR2 (ps, npLen);

        _MYS_TCHAR* ps2 = (_MYS_TCHAR*)m_mem.Alloc ((npLen + 1) * sizeof (_MYS_TCHAR)) + npLen;

        *ps2-- = '\0';
        for (; npLen > 0; ps2--, ps++, npLen--)
            *ps2 = *ps;

        ASSERT (ps2 == (const _MYS_TCHAR*)m_mem.GetPtr () - 1);
    }

    return *this;
}

void _MY_STRING::AddFormatText (const _MYS_TCHAR* szFormat, ...)
{
    ASSERT_R_STR (szFormat);

    _MY_STRING str;

    va_list argList;
    va_start (argList, szFormat);
    str.FormatV (szFormat, argList);
    va_end (argList);

    AddText (str.GetText ());
}

void _MY_STRING::AddFormatLine (const _MYS_TCHAR* szFormat, ...)
{
    ASSERT_R_STR (szFormat);

    _MY_STRING str;

    va_list argList;
    va_start (argList, szFormat);
    str.FormatV (szFormat, argList);
    va_end (argList);

    AddText (str.GetText ());
    AddEmptyLine ();
}

void _MY_STRING::InsertLineBeginLeaderSpaces (const INT_P npNumLeaderSpaces)
{
    if (npNumLeaderSpaces <= 0 || IsEmpty ())
        return;

    _MY_STRING str;
    const _MYS_TCHAR* psBegin = GetText ();

    while (TRUE)
    {
        const _MYS_TCHAR* ps = _MYS_STRCHR (psBegin, '\n');
        if (ps == NULL)
        {
            if (*SkipSpaces (psBegin) != '\0')  // 不为全空白行?
                str.AddChar (' ', npNumLeaderSpaces);
            str.AddText (psBegin);
            break;
        }

        ps++;

        if (SkipSpaces (psBegin, ps) < ps)  // 不为全空白行?
            str.AddChar (' ', npNumLeaderSpaces);
        str.AddText (psBegin, ps - psBegin);

        psBegin = ps;
    }

    SetText (str.GetText ());
}

void _MY_STRING::RemoveChar (const INT_P npIndex, INT_P npLen)
{
    ASSERT (npIndex >= 0 && npIndex <= GetLength () && npLen >= 0);

    if (npIndex + npLen > GetLength ())
        npLen = GetLength () - npIndex;

    CheckConvertConstText ().Remove (npIndex * sizeof (_MYS_TCHAR), npLen * sizeof (_MYS_TCHAR));
}

void _MY_STRING::RemoveAllSpaceLines ()
{
    if (IsEmpty ())
        return;

    _MY_STRING str;
    const _MYS_TCHAR* psBegin = GetText ();

    while (TRUE)
    {
        const _MYS_TCHAR* ps = _MYS_STRCHR (psBegin, '\n');
        if (ps == NULL)
        {
            if (*SkipSpaces (psBegin) != '\0')  // 不为全空白行?
                str.AddText (psBegin);
            break;
        }

        ps++;

        if (SkipSpaces (psBegin, ps) < ps)  // 不为全空白行?
            str.AddText (psBegin, ps - psBegin);

        psBegin = ps;
    }

    SetText (str.GetText ());
}

const _MYS_TCHAR* _MY_STRING::RemoveEndPathChar ()
{
    do
    {
        const INT_P npLength = GetLength ();
        if (npLength <= 1)  // 为空或者只有1个字符?
            break;

        const _MYS_TCHAR* ps = GetText ();
        ASSERT (npLength >= 2);  // 前面检查过
        if (ps [npLength - 1] != OS_PATH_CHAR)  // 不以路径字符结束?
            break;

    #if defined (_PF_WINDOWS)
        if (ps [npLength - 2] == ':')  // 避免删除驱动器符后的路径字符
            break;
    #endif

        RemoveChar (npLength - 1);
    }
    while (FALSE);

    return GetText ();
}

void _MY_STRING::AddFormatTextWithLeaderSpaces (const INT_P npNumLeaderSpaces, const _MYS_TCHAR* szFormat, ...)
{
    ASSERT (npNumLeaderSpaces >= 0);
    MCHECK_STR_POINTER (szFormat)
    ASSERT_R_STR (szFormat);

    _MY_STRING str;

    va_list argList;
    va_start (argList, szFormat);
    str.FormatV (szFormat, argList);
    va_end (argList);

    str.InsertLineBeginLeaderSpaces (npNumLeaderSpaces);

    AddText (str.GetText ());
}

void _MY_STRING::AddFormatLineWithLeaderSpaces (const INT_P npNumLeaderSpaces, const _MYS_TCHAR* szFormat, ...)
{
    ASSERT (npNumLeaderSpaces >= 0);
    MCHECK_STR_POINTER (szFormat)
    ASSERT_R_STR (szFormat);

    _MY_STRING str;

    va_list argList;
    va_start (argList, szFormat);
    str.FormatV (szFormat, argList);
    va_end (argList);

    str.InsertLineBeginLeaderSpaces (npNumLeaderSpaces);

    AddText (str.GetText ());
    AddEmptyLine ();
}

_MY_STRING _MY_STRING::Left (INT_P npCount) const
{
    ASSERT (npCount >= 0);

    _MY_STRING str;

    npCount = MIN (npCount, GetLength ());
    if (npCount > 0)
    {
        str.m_mem.Append (GetText (), npCount * sizeof (_MYS_TCHAR));
        str.m_mem._MYS_MEM_ADD_CHAR ('\0');
    }

    return str;
}

_MY_STRING _MY_STRING::Right (INT_P npCount) const
{
    ASSERT (npCount >= 0);

    _MY_STRING str;

    const INT_P npLength = GetLength ();
    npCount = MIN (npCount, npLength);
    if (npCount > 0)
        str.m_mem.Append (GetText () + (npLength - npCount), (npCount + 1) * sizeof (_MYS_TCHAR));

    return str;
}

_MY_STRING _MY_STRING::Middle (INT_P npIndex, INT_P npCount) const
{
    ASSERT (npIndex >= 0 && npIndex <= GetLength () && npCount >= 0);

    const INT_P npLength = GetLength ();
    const INT_P npEndIndex = npIndex + npCount;

    npIndex = CLIP (npIndex, 0, npLength);
    npCount = CLIP (npEndIndex, 0, npLength) - npIndex;

    _MY_STRING str;
    if (npCount > 0)
    {
        str.m_mem.Append (GetText () + npIndex, npCount * sizeof (_MYS_TCHAR));
        str.m_mem._MYS_MEM_ADD_CHAR ('\0');
    }

    return str;
}

_MY_STRING& _MY_STRING::MakeUpper ()
{
    _MYS_TCHAR* ps = (_MYS_TCHAR*)CheckConvertConstText ().GetPtr ();
    const INT_P npLength = GetLength ();

    for (INT_P i = 0; i < npLength; i++, ps++)
    {
        const UINT_P upChar = (UINT_P)*ps;

        if (upChar >= 'a' && upChar <= 'z')
            *ps = (_MYS_TCHAR)(upChar - 'a' + 'A');
    }

    return *this;
}

_MY_STRING& _MY_STRING::MakeLower ()
{
    _MYS_TCHAR* ps = (_MYS_TCHAR*)CheckConvertConstText ().GetPtr ();
    const INT_P npLength = GetLength ();

    for (INT_P i = 0; i < npLength; i++, ps++)
    {
        const UINT_P upChar = (UINT_P)*ps;

        if (upChar >= 'A' && upChar <= 'Z')
            *ps = (_MYS_TCHAR)(upChar - 'A' + 'a');
    }

    return *this;
}

void _MY_STRING::MakeFirstLetterLower ()
{
    if (IsEmpty ())
        return;

    _MYS_TCHAR* ps = (_MYS_TCHAR*)CheckConvertConstText ().GetPtr ();
    const UINT_P upChar = (UINT_P)*ps;

    if (upChar >= 'A' && upChar <= 'Z')
        *ps = (_MYS_TCHAR)(upChar - 'A' + 'a');
}

void _MY_STRING::MakeFirstLetterUpper ()
{
    if (IsEmpty ())
        return;

    _MYS_TCHAR* ps = (_MYS_TCHAR*)CheckConvertConstText ().GetPtr ();
    const UINT_P upChar = (UINT_P)*ps;

    if (upChar >= 'a' && upChar <= 'z')
        *ps = (_MYS_TCHAR)(upChar - 'a' + 'A');
}

_MY_STRING& _MY_STRING::TrimLeft ()
{
    _MYS_TCHAR* ps = (_MYS_TCHAR*)CheckConvertConstText ().GetPtr ();
    const INT_P npLength = GetLength ();

    INT_P i;
    for (i = 0; i < npLength; i++)
    {
        if (IS_SPACE_CHAR_NOT_CHECK_ZERO (ps [i]) == FALSE)
            break;
    }

    if (i > 0)
    {
        const INT_P npDataSize = (npLength - i + 1) * sizeof (_MYS_TCHAR);
        memmove (ps, ps + i, npDataSize);
        m_mem.Realloc (npDataSize);
    }

    return *this;
}

_MY_STRING& _MY_STRING::TrimRight ()
{
    _MYS_TCHAR* ps = (_MYS_TCHAR*)CheckConvertConstText ().GetPtr ();
    const INT_P npLength = GetLength ();

    INT_P i;
    for (i = npLength - 1; i >= 0; i--)
    {
        if (IS_SPACE_CHAR_NOT_CHECK_ZERO (ps [i]) == FALSE)
            break;
    }

    if (i + 1 != npLength)
    {
        m_mem.Realloc ((i + 1) * sizeof (_MYS_TCHAR));
        m_mem._MYS_MEM_ADD_CHAR ('\0');
    }

    return *this;
}

_MY_STRING& _MY_STRING::TrimAllSpaces ()
{
    _MYS_TCHAR* ps = (_MYS_TCHAR*)CheckConvertConstText ().GetPtr ();
    const INT_P npLength = GetLength ();

    if (npLength > 0)
    {
        CVolMem memNew;
        _MYS_TCHAR* psBegin = (_MYS_TCHAR*)memNew.Alloc (npLength * sizeof (_MYS_TCHAR));
        _MYS_TCHAR* psDest = psBegin;

        for (INT_P i = 0; i < npLength; i++)
        {
            if (IS_SPACE_CHAR_NOT_CHECK_ZERO (ps [i]) == FALSE)
                *psDest++ = ps [i];
        }

        const INT_P npNewLength = psDest - psBegin;
        ASSERT (npNewLength <= npLength);

        if (npNewLength < npLength)
        {
            ps = (_MYS_TCHAR*)m_mem.Alloc ((npNewLength + 1) * sizeof (_MYS_TCHAR));

            memcpy (ps, psBegin, npNewLength * sizeof (_MYS_TCHAR));
            ps [npNewLength] = '\0';
        }
    }

    return *this;
}

// 计算返回根据指定format生成文本的可能最大长度.
INT_P _MY_STRING::sCalcMaxLen (const _MYS_TCHAR* szFormat, va_list argList)
{
    ASSERT_R_STR (szFormat);

#ifdef __MS_CPP__  // Compiling with VC++?

    INT_P npMaxLen = _MYS_VSCPRINTF (szFormat, argList);

#else

    INT_P npMaxLen = 0;

    CVolMem memTemp;
    const _MYS_TCHAR* ps;

    // 获取最多可能需要分配的内存尺寸
    for (ps = szFormat; *ps != '\0'; ps++)
    {
        // 管理'%'字符
        if (*ps != '%')
        {
            npMaxLen++;
            continue;
        }

        ps++;

        // 跳过'%%'
        if (*ps == '%')
        {
            npMaxLen++;
            continue;
        }

        //-----------------------------------------------

        INT_P npItemLen = 0;

        // 管理格式指定
        INT_P npWidth = 0;
        for (; *ps != '\0'; ps++)
        {
            // 检查是否有效的标记
            if (*ps == '#')
                npMaxLen += 2;   // '0x'
            else if (*ps == '*')
                npWidth = va_arg (argList, INT);
            else if (*ps == '-' || *ps == '+' || *ps == '0' || *ps == ' ')
                ;
            else
                break;
        }

        // 获取宽度并跳过该指定符
        if (npWidth == 0)
        {
            // width indicated by
            npWidth = _MYS_TTOI (ps);
            while (*ps != '\0' && IS_NUMBER_CHAR (*ps))
                ps++;
        }
        ASSERT (npWidth >= 0);

        INT_P npPrecision = 0;
        if (*ps == '.')
        {
            // 跳过'.'指定符(width.precision)
            ps++;

            // 获取精度并跳过该指定符
            if (*ps == '*')
            {
                npPrecision = va_arg (argList, INT);
                ps++;
            }
            else
            {
                npPrecision = _MYS_TTOI (ps);
                while (*ps != '\0' && IS_NUMBER_CHAR (*ps))
                    ps++;
            }
            ASSERT (npPrecision >= 0);
        }

        // 处理类型指定符
        switch (*ps)
        {
        // 忽略字符类型指定，强制都为unicode字符
        case 'h':
        case 'l':
        case 'F':
        case 'N':
        case 'L':
            ps++;
            break;
        }

        switch (*ps)
        {
        case 'c':
        case 'C':
            npItemLen = 2;
            // va_arg (argList, _MYS_TCHAR);  // 此行gcc会报警告，用下行替换. 
            va_arg (argList, INT);
            break;

        case 's':  {
            _MYS_TCHAR* pstrNextArg = va_arg (argList, _MYS_TCHAR*);
            MCHECK_STR_POINTER (pstrNextArg)
            if (pstrNextArg == NULL)
               npItemLen = 6;  // "(null)"
            else
               npItemLen = MAX (1, _MYS_STRLEN (pstrNextArg));
            break;  }
        }

        // 调整文本长度
        if (npItemLen != 0)
        {
            if (npPrecision != 0)
                npItemLen = MIN (npItemLen, npPrecision);
            npItemLen = MAX (npItemLen, npWidth);
        }
        else
        {
            switch (*ps)
            {
            // 整数
            case 'd':
            case 'i':
            case 'o':
            case 'u':
            case 'x':
            case 'X':
                va_arg (argList, INT);
                npItemLen = MAX (32, npWidth + npPrecision);
                break;

            case 'f':
            case 'e':
            case 'E':
            case 'g':
            case 'G':
                va_arg (argList, double);
                // 312 == strlen("-1+(309 zeroes).")
                // 309 zeroes == MAX precision of a double
                // 6 == adjustment in case precision is not specified,
                //   which means that the precision defaults to 6
                npItemLen = MAX (312 + 6, npWidth) + npPrecision;
                break;

            case 'p':
                va_arg (argList, void*);
                npItemLen = MAX (32, npWidth + npPrecision);
                break;

            // 不输出
            case 'n':
                va_arg (argList, INT*);
                break;

            DEFAULT_FAIL  // 未知格式选项
            }
        }

        // 调整npMaxLen
        npMaxLen += npItemLen;
    }
#endif

    return npMaxLen;
}

void _MY_STRING::FormatV (const _MYS_TCHAR* szFormat, va_list argList)
{
    MCHECK_STR_POINTER (szFormat)
    ASSERT_R_STR (szFormat);

    va_list argList2;
#ifdef __MS_CPP__  // Compiling with VC++?
    argList2 = argList;
#else
    va_copy (argList2, argList);
#endif

    //-----------------------------------------------

    Empty ();

    const INT_P npMaxLen = sCalcMaxLen (szFormat, argList);

    if (npMaxLen > 0)
    {
        const INT_P npLen = _MYS_VSTPRINTF ((_MYS_TCHAR*)m_mem.Alloc ((npMaxLen + 1) * sizeof (_MYS_TCHAR)), szFormat, argList2);

        if (npLen <= 0)  // 失败或者为0?
        {
            Empty ();
        }
        else
        {
            ASSERT (npLen <= npMaxLen);
            m_mem.Realloc ((npLen + 1) * sizeof (_MYS_TCHAR));  // 删除过多的空余内存
        }
    }

    va_end (argList2);
}

_MY_STRING& _MY_STRING::Format (const _MYS_TCHAR* szFormat, ...)
{
    va_list argList;
    va_start (argList, szFormat);
    FormatV (szFormat, argList);
    va_end (argList);

    return *this;
}

void _MY_STRING::CheckAddCRLF ()
{
    CheckConvertConstText ();

    // 获得尾部的字符
    const _MYS_TCHAR chLast =
            (m_mem.GetSize () < (INT_P)sizeof (_MYS_TCHAR) * 2 ? '\0' :  // 文本为空?
                *((const _MYS_TCHAR*)m_mem.GetEndPtr () - 2));

    if (chLast != '\n')
    {
        if (chLast != '\r')
            AddText (_MYS_T ("\r\n"));
        else
            AddChar ('\n');
    }
}

#if (defined (_MY_WSTRING_IMPL) && defined (_UNICODE))  // 为实现宽文本对象且为编译Unicode版本?

COMPILE_TIME_ASSERT (sizeof (_MYS_TCHAR) == sizeof (TCHAR));

_MY_STRING& _MY_STRING::BJ2QJ ()
{
    if (IsEmpty ())
        return *this;

    _MYS_TCHAR* ps = (_MYS_TCHAR*)CheckConvertConstText ().GetPtr ();
    while (*ps != '\0')
    {
        const UINT_P upChar = (UINT_P)*ps;

        if (upChar == ' ')
        {
            *ps = (TCHAR)0x3000;
        }
        else if (upChar == 0x2E)
        {
            *ps = (TCHAR)0x3002;
        }
        else if (upChar >= 33 && upChar <= 126)
        {
            *ps = (TCHAR)(upChar + 65248);
        }

        ps++;
    }

    return *this;
}

_MY_STRING& _MY_STRING::QJ2BJ ()
{
    if (IsEmpty ())
        return *this;

    _MYS_TCHAR* ps = (_MYS_TCHAR*)CheckConvertConstText ().GetPtr ();
    while (*ps != '\0')
    {
        const UINT_P upChar = (UINT_P)*ps;

        if (upChar == 0x3000)
        {
            *ps = ' ';
        }
        else if (upChar == 0x3002)
        {
            *ps = 0x2E;
        }
        else if (upChar >= 65281 && upChar <= 65374)
        {
            *ps = (_MYS_TCHAR)(upChar - 65248);
        }

        ps++;
    }

    return *this;
}

#endif

INT_P _MY_STRING::SearchText (const _MYS_TCHAR* szSearch, INT_P npBeginIndex, const BOOL_P blpCaseInsensitive, const BOOL_P blpReverseFind)
{
    ASSERT_R_STR (szSearch);

    const _MYS_TCHAR* psText = GetText ();
    INT_P npTextLength = GetLength ();

    if (npBeginIndex > npTextLength)  // 起始索引位置超出最大位置?
        return -1;

    if (blpReverseFind == FALSE)  // 正向查找?
    {
        if (npBeginIndex <= 0)  // 使用默认查找起始位置?
        {
            npBeginIndex = 0;
        }
        else
        {
            psText += npBeginIndex;
            npTextLength -= npBeginIndex;
        }
    }
    else  // 逆向查找
    {
        if (npBeginIndex < 0)  // 使用默认查找起始位置?
            npBeginIndex = npTextLength;
        else
            npTextLength = npBeginIndex;
    }

    if (IsEmptyStr (szSearch))
        return npBeginIndex;

    if (npTextLength <= 0)
        return -1;

    const _MYS_TCHAR* psFound = FindString (psText, npTextLength, szSearch, _MYS_STRLEN (szSearch), blpCaseInsensitive, blpReverseFind);
    if (psFound == NULL)
        return -1;
    
    const INT_P npIndex = psFound - GetText ();
    ASSERT (npIndex >= 0 && npIndex <= GetLength ());
    return npIndex;
}

_MYS_TCHAR _MY_STRING::sGetBase64EncodeChar (BYTE bt, const INT_P npEncodeType)
{
    static const _MYS_TCHAR* cs_szEnBase64Tab = _MYS_T ("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/");  // 标准Base64编码

    ASSERT (bt >= 0 && bt < 64);
    _MYS_TCHAR ch = cs_szEnBase64Tab [bt];

    if (npEncodeType == 1)  // URL专用Base64编码?
    {
        if (ch == '+')
            ch = '-';
        else if (ch == '/')
            ch = '_';
    }
    else if (npEncodeType == 2)  // 正则专用Base64编码
    {
        if (ch == '+')
            ch = '!';
        else if (ch == '/')
            ch = '-';
    }

    return ch;
}

_MY_STRING& _MY_STRING::EncodeBase64 (const BYTE* pData, const INT_P npDataSize, INT_P npMaxLineLen, const INT_P npEncodeType)
{
    ASSERT_R_ADR (pData, npDataSize);

    if (npMaxLineLen == 0)  // 使用默认每行最多字符数?
        npMaxLineLen = 76;

    BYTE c1, c2, c3;
    INT_P npDstLen = 0;  // 输出的字符计数
    INT_P npLineLen = 0;  // 输出的行长度计数
    const INT_P npDiv = npDataSize / 3;  // 输入数据长度除以3得到的倍数
    const INT_P npMod = npDataSize % 3;  // 输入数据长度除以3得到的余数
    const BYTE* pEnd = pData + npDataSize;
 
    // 分配足够容纳最大编码文本的内容空间
    Empty ();
    _MYS_TCHAR* psDest = (_MYS_TCHAR*)m_mem.Alloc (sizeof (_MYS_TCHAR) * (npDiv * (4 + 2) + 4 + 1));

    for (INT_P npIndex = 0; npIndex < npDiv; npIndex++)
    {
        // 取3个字节
        c1 = *pData++;
        c2 = *pData++;
        c3 = *pData++;
 
        // 编码成4个字符
        *psDest++ = sGetBase64EncodeChar ((c1 >> 2), npEncodeType);
        *psDest++ = sGetBase64EncodeChar ((((c1 << 4) | (c2 >> 4)) & 0x3f), npEncodeType);
        *psDest++ = sGetBase64EncodeChar ((((c2 << 2) | (c3 >> 6)) & 0x3f), npEncodeType);
        *psDest++ = sGetBase64EncodeChar ((c3 & 0x3f), npEncodeType);

        if (npMaxLineLen > 0 && npLineLen + 4 + 4 > npMaxLineLen)  // 需要输出换行(无法容纳下一次转换)?
        {
            if (pData < pEnd)
            {
                *psDest++ = '\r';
                *psDest++ = '\n';
            }
            npLineLen = 0;
        }
        else
            npLineLen += 4;
    }
 
    // 编码余下的字节
    if (npMod == 1)
    {
        c1 = *pData;
        *psDest++ = sGetBase64EncodeChar (((c1 & 0xfc) >> 2), npEncodeType);
        *psDest++ = sGetBase64EncodeChar ((((c1 & 0x03) << 4)), npEncodeType);
        *psDest++ = '=';
        *psDest++ = '=';
    }
    else if (npMod == 2)
    {
        c1 = *pData++;
        c2 = *pData;
        *psDest++ = sGetBase64EncodeChar (((c1 & 0xfc) >> 2), npEncodeType);
        *psDest++ = sGetBase64EncodeChar ((((c1 & 0x03) << 4) | ((c2 & 0xf0) >> 4)), npEncodeType);
        *psDest++ = sGetBase64EncodeChar ((((c2 & 0x0f) << 2)), npEncodeType);
        *psDest++ = '=';
    }
 
    *psDest++ = '\0';  // 输出结束符

    ASSERT ((BYTE*)psDest <= m_mem.GetEndPtr ());
    m_mem.Realloc ((BYTE*)psDest - m_mem.GetPtr ());  // 去除多余的字符
 
    return *this;
}

UINT_P _MY_STRING::sGetBase64DecodeByte (_MYS_TCHAR ch, const INT_P npEncodeType)
{
    static const BYTE cs_abtDeBase64Tab [] =
    {
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        62,  // '+'
        0, 0, 0,
        63,  // '/'
        52, 53, 54, 55, 56, 57, 58, 59, 60, 61,  // '0'-'9'
        0, 0, 0, 0, 0, 0, 0,
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
        13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25,  // 'A'-'Z'
        0, 0, 0, 0, 0, 0,
        26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38,
        39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51  // 'a'-'z'
    };
    COMPILE_TIME_ASSERT (NUM_ELEMENTS_OF (cs_abtDeBase64Tab) == 123);

    if (npEncodeType == 1)  // URL专用Base64编码?
    {
        if (ch == '-')
            ch = '+';
        else if (ch == '_')
            ch = '/';
    }
    else if (npEncodeType == 2)  // 正则专用Base64编码
    {
        if (ch == '!')
            ch = '+';
        else if (ch == '-')
            ch = '/';
    }

    if (ch < 0 || ch >= NUM_ELEMENTS_OF (cs_abtDeBase64Tab))
        return 0;

    return cs_abtDeBase64Tab [ch];
}

CVolMem& _MY_STRING::sDecodeBase64 (const _MYS_TCHAR* psSrc, INT_P npSrcLen, CVolMem& memResult, const INT_P npEncodeType)
{
    if (npSrcLen < 0)
        npSrcLen = _MYS_STRLEN (psSrc);

    if (npSrcLen == 0)
    {
        memResult.Free ();
        return memResult;
    }

    ASSERT_R_STR2 (psSrc, npSrcLen);
    const _MYS_TCHAR* psEnd = psSrc + npSrcLen;

    BYTE* pbDest = memResult.Alloc (sizeof (BYTE) * (npSrcLen / 4 * 3 + 4));
 
    // 取4个字符,解码到一个整数,再经过移位得到3个字节.
    while (psSrc < psEnd)
    {
        if (*psSrc != '\r' && *psSrc != '\n')
        {
            UINT_P upValue = (sGetBase64DecodeByte (*psSrc++, npEncodeType) << 18);

            if (psSrc >= psEnd)
                break;
            upValue += (sGetBase64DecodeByte (*psSrc++, npEncodeType) << 12);
            ASSERT (memResult.IsInside (pbDest, sizeof (BYTE)));
            *pbDest++ = (BYTE)((upValue & 0x00ff0000) >> 16);
 
            if (psSrc >= psEnd || *psSrc == '=')
                break;
            upValue += (sGetBase64DecodeByte (*psSrc++, npEncodeType) << 6);
            ASSERT (memResult.IsInside (pbDest, sizeof (BYTE)));
            *pbDest++ = (BYTE)((upValue & 0x0000ff00) >> 8);
 
            if (psSrc >= psEnd || *psSrc == '=')
                break;
            upValue += sGetBase64DecodeByte (*psSrc++, npEncodeType);
            ASSERT (memResult.IsInside (pbDest, sizeof (BYTE)));
            *pbDest++ = (BYTE)(upValue & 0x000000ff);
        }
        else
        {
            psSrc++;  // 跳过回车/换行
        }
    }
  
    ASSERT (pbDest <= memResult.GetEndPtr ());
    memResult.Realloc (pbDest - memResult.GetPtr ());  // 去除多余的数据
    return memResult;
}

_MY_STRING& _MY_STRING::EncodeQuoted (const BYTE* pData, const INT_P npDataSize, INT_P npMaxLineLen)
{
    ASSERT_R_ADR (pData, npDataSize);

    if (npMaxLineLen == 0)  // 使用默认每行最多字符数?
    {
        npMaxLineLen = 76 - 3;
    }
    else if (npMaxLineLen > 0)
    {
        npMaxLineLen -= 3;

        if (npMaxLineLen < 0)
            npMaxLineLen = 0;
    }

    // 分配足够容纳最大编码文本的内容空间
    Empty ();
    _MYS_TCHAR* psDest = (_MYS_TCHAR*)m_mem.Alloc (sizeof (_MYS_TCHAR) * (npDataSize * 6 + 1));

    INT_P npLineLen = 0;

    for (INT_P npIndex = 0; npIndex < npDataSize; npIndex++, pData++)
    {
        ASSERT ((BYTE*)(psDest + 6) < m_mem.GetEndPtr ());

        const UINT_P upChar = *pData;

        // ASCII 33-60, 62-126原样输出,其余的需编码.
        if (upChar >= '!' && upChar <= '~' && upChar != '=')
        {
            *psDest++ = (U8CHAR)upChar;
            npLineLen++;
        }
        else
        {
            *psDest++ = '=';
            Byte2TwoHexChars (upChar, psDest);
            psDest += 2;

            npLineLen += 3;
        }
 
        if (npMaxLineLen >= 0 && npLineLen > npMaxLineLen)  // 输出换行?
        {
            // 加入软回车标志
            *psDest++ = '=';
            *psDest++ = '\r';
            *psDest++ = '\n';

            npLineLen = 0;
        }
    }

    ASSERT ((BYTE*)(psDest + 1) <= m_mem.GetEndPtr ());
    *psDest++ = '\0';  // 输出结束符

    m_mem.Realloc ((BYTE*)psDest - m_mem.GetPtr ());  // 去除多余的字符
    return *this;
}

CVolMem& _MY_STRING::sDecodeQuoted (const _MYS_TCHAR* psSrc, INT_P npSrcLen, CVolMem& memResult)
{
    if (npSrcLen < 0)
        npSrcLen = _MYS_STRLEN (psSrc);

    if (npSrcLen == 0)
    {
        memResult.Free ();
        return memResult;
    }

    ASSERT_R_STR2 (psSrc, npSrcLen);
    const _MYS_TCHAR* psEnd = psSrc + npSrcLen;

    BYTE* pbDest = memResult.Alloc (npSrcLen);
    while (psSrc < psEnd)
    {
        ASSERT (pbDest < memResult.GetEndPtr ());

        if (psSrc + 3 <= psEnd && *psSrc == '=')  // 为编码字节?
        {
            if (psSrc [1] != '\r' || psSrc [2] != '\n')  // 不为软回车?
                *pbDest++ = (BYTE)((HexCharToValue (psSrc [1]) << 4) | HexCharToValue (psSrc [2]));

            psSrc += 3;
        }
        else  // 非编码字节
        {
            *pbDest++ = (BYTE)*psSrc++;
        }
    }

    ASSERT (pbDest <= memResult.GetEndPtr ());
    memResult.Realloc (pbDest - memResult.GetPtr ());  // 去除多余的数据

    return memResult;
}

_MY_STRING& _MY_STRING::ReadFromFile (const TCHAR* szFileName, const INT_P npReadDataSize, VOL_STRING_ENCODE_TYPE enEncodeType, BOOL_P* pblpReadSucceeded)
{
    ASSERT_R_STR (szFileName);

    Empty ();

    // 多读入3个字节,用作处理MS的文本文件起始标志.
    CVolMem memBuf1;
    INT_P npRealReadedDataSize = memBuf1.ReadFromFile (
            szFileName, (npReadDataSize >= 0 ? 3 + npReadDataSize : -1));

    if (npRealReadedDataSize > 0)
    {
        if (pblpReadSucceeded != NULL)
            *pblpReadSucceeded = TRUE;

        memBuf1.AddDWord (0);  // 添加一个结束零DWORD
        BYTE* pb = memBuf1.GetPtr ();

        if (*(WORD*)pb == 0xFEFF)  // 为MS的Unicode文本文件起始标志?
        {
            pb += sizeof (WORD);
            npRealReadedDataSize -= sizeof (WORD);
            enEncodeType = VSET_UTF_16;
        }
        else if (pb [0] == 0xEF && pb [1] == 0xBB && pb [2] == 0xBF)  // 为MS的Utf-8文本文件起始标志?
        {
            pb += 3;
            npRealReadedDataSize -= 3;
            enEncodeType = VSET_UTF_8;
        }
        else
        {
            if (enEncodeType == VSET_UNKNOWN)
                enEncodeType = VSET_MBCS;
        }

        if (npReadDataSize >= 0 && npRealReadedDataSize > npReadDataSize)  // 读入了多余的数据?
        {
            ASSERT (memBuf1.IsInside (pb + npReadDataSize, sizeof (DWORD)));  // 前面的算法决定
            *(DWORD*)(pb + npReadDataSize) = 0;  // 将其去除
        }

        CVolMem memBuf2;
        if (enEncodeType == VSET_MBCS)
        {
            pb = (BYTE*)GetWideText ((const CHAR*)pb, memBuf2, NULL);
            enEncodeType = VSET_UTF_16;
        }

        switch (enEncodeType)
        {
        case VSET_UTF_16:
            SetText ((WCHAR*)pb);
            break;

        case VSET_UTF_8:
            SetText ((U8CHAR*)pb);
            break;

        DEFAULT_FAIL
        }
    }
    else
    {
        if (pblpReadSucceeded != NULL)
            *pblpReadSucceeded = FALSE;
    }
    
    return *this;
}

BOOL_P _MY_STRING::WriteIntoFile (const TCHAR* szFileName, INT_P npWriteStrLength, const VOL_STRING_ENCODE_TYPE enEncodeType) const
{
    ASSERT_R_STR (szFileName);

    const INT_P npStrLength = GetLength ();
    if (npWriteStrLength < 0 || npWriteStrLength > npStrLength)
        npWriteStrLength = npStrLength;

    const BYTE* pb = (const BYTE*)GetText ();
    INT_P npDataSize = npWriteStrLength * sizeof (_MYS_TCHAR);

    switch (enEncodeType)
    {
    case VSET_MBCS:
    case VSET_UTF_16:  {
    #ifndef _MY_WSTRING_IMPL
        CWString str;
        str.SetText (GetText (), npWriteStrLength);
        pb = (const BYTE*)str.GetText ();
    #endif

        CVolMem memBuf;
        if (enEncodeType != VSET_MBCS)
        {
        #ifndef _MY_WSTRING_IMPL
            npDataSize = str.GetLength () * sizeof (WCHAR);
        #endif
            memBuf.AddWord (0xFEFF);  // 添加MS的unicode文本文件起始标志
            memBuf.Append (pb, npDataSize);
            return memBuf.WriteIntoFile (szFileName);
        }
        else
        {
        #ifdef _MY_WSTRING_IMPL
            CWString str;
            if (npWriteStrLength != npStrLength)
            {
                str.SetText (GetText (), npWriteStrLength);
                pb = (const BYTE*)str.GetText ();
            }
        #endif

            pb = (BYTE*)GetMbsText ((const WCHAR*)pb, memBuf, &npDataSize);
            return WriteDataIntoFile (szFileName, pb, npDataSize * sizeof (CHAR));
        }  }

    case VSET_UTF_8:  {
    #ifdef _MY_WSTRING_IMPL
        CU8String str;
        str.SetText (GetText (), npWriteStrLength);
        pb = (const BYTE*)str.GetText ();
        npDataSize = str.GetLength () * sizeof (U8CHAR);
    #endif
        return WriteDataIntoFile (szFileName, pb, npDataSize);  }
    }

    return FALSE;
}

_MY_STRING& _MY_STRING::FormatDateTime (DATE dt, const TCHAR* szFormat)
{
    UDATE ud;
    if (IsEmptyStr (szFormat) == FALSE && VarUdateFromDate (dt, 0, &ud) == S_OK)
    {
        struct tm tmTemp;
        tmTemp.tm_sec	= ud.st.wSecond;
        tmTemp.tm_min	= ud.st.wMinute;
        tmTemp.tm_hour	= ud.st.wHour;
        tmTemp.tm_mday	= ud.st.wDay;
        tmTemp.tm_mon	= ud.st.wMonth - 1;
        tmTemp.tm_year	= ud.st.wYear - 1900;
        tmTemp.tm_wday	= ud.st.wDayOfWeek;
        tmTemp.tm_yday	= ud.wDayOfYear - 1;
        tmTemp.tm_isdst	= 0;

        TCHAR buf [512];
        buf [0] ='\0';
        _tcsftime (buf, NUM_ELEMENTS_OF (buf) - 2, szFormat, &tmTemp);

        SetText (buf);
    }

    return *this;
}

_MY_STRING operator+ (const _MY_STRING& string1, const _MY_STRING& string2)
{
    if (string1.IsEmpty ())
        return string2;

    if (string2.IsEmpty ())
        return string1;

    _MY_STRING str;
    str.m_mem.AddOnlyText (string1.GetText ());
    str.m_mem.AddString (string2.GetText ());

    return str;
}

_MY_STRING operator+ (const _MY_STRING& string, const _MYS_TCHAR ch)
{
    if (ch == '\0')
        return string;

    _MY_STRING str;
    str.m_mem.AddString (string.GetText ());
    str.AddChar (ch);

    return str;
}

_MY_STRING operator+ (const _MY_STRING& string, const _MYS_TCHAR* ps)
{
    ASSERT_R_STR (ps);

    if (IsEmptyStr (ps))
        return string;

    _MY_STRING str;
    str.m_mem.AddString (string.GetText ());
    str.AddText (ps);

    return str;
}

_MY_STRING operator+ (const _MYS_TCHAR* ps, const _MY_STRING& string)
{
    ASSERT_R_STR (ps);

    if (IsEmptyStr (ps))
        return string;

    if (string.IsEmpty ())
        return _MY_STRING (ps);

    _MY_STRING str;
    str.m_mem.Append (ps, _MYS_STRLEN (ps) * sizeof (_MYS_TCHAR));
    str.m_mem.AddString (string.GetText ());

    return str;
}

_MY_STRING operator+ (const _MYS_TCHAR ch, const _MY_STRING& string)
{
    if (ch == '\0')
        return string;

    if (string.IsEmpty ())
        return _MY_STRING (ch);

    _MY_STRING str;
    str.m_mem._MYS_MEM_ADD_CHAR (ch);
    str.m_mem.AddString (string.GetText ());

    return str;
}

//----------------------------------------------------------------------------------

void _MY_BUF_STRING::SetText (const _MYS_TCHAR* szText)
{
    ASSERT_R_STR (szText);

    if (IsEmptyStr (szText))
    {
        Empty ();
    }
    else if (_MYS_STRLEN (szText) < NUM_ELEMENTS_OF (m_acBuf))
    {
        m_str.Empty ();
        _MYS_STRCPY (m_acBuf, szText);
    }
    else
    {
        m_str.SetText (szText);
        m_acBuf [0] = '\0';
    }
}

void _MY_BUF_STRING::SetText (const _MYS_TCHAR* psText, const INT_P npLength)
{
    if (npLength <= 0)
    {
        Empty ();
    }
    else
    {
        ASSERT_R_STR2 (psText, npLength);

        if (npLength < NUM_ELEMENTS_OF (m_acBuf))
        {
            m_str.Empty ();
            memcpy (m_acBuf, psText, sizeof (_MYS_TCHAR) * npLength);
            m_acBuf [npLength] = '\0';
        }
        else
        {
            m_str.SetText (psText, npLength);
            m_acBuf [0] = '\0';
        }
    }
}

//----------------------------------------------------------------------------------

CVolBaseInputStream& operator>> (CVolBaseInputStream& stream, _MY_STRING_WITH_HASH& strWithHash)
{
    stream >> strWithHash.m_str >> strWithHash.m_dwHash;
    return stream;
}

CVolBaseOutputStream& operator<< (CVolBaseOutputStream& stream, const _MY_STRING_WITH_HASH& strWithHash)
{
    stream << strWithHash.m_str << strWithHash.m_dwHash;
    return stream;
}

CVolBaseInputStream& operator>> (CVolBaseInputStream& stream, _MY_STRING_WITH_IHASH& strWithIHash)
{
    stream >> strWithIHash.m_str >> strWithIHash.m_dwIHash;
    return stream;
}

CVolBaseOutputStream& operator<< (CVolBaseOutputStream& stream, const _MY_STRING_WITH_IHASH& strWithIHash)
{
    stream << strWithIHash.m_str << strWithIHash.m_dwIHash;
    return stream;
}
