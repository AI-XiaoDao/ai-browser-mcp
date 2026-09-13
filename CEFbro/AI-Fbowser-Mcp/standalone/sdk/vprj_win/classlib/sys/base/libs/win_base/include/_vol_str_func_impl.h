
// Copyright (C) Recursion Company. All rights reserved.

#include "_vol_str_macro.h"

//----------------------------------------------------------------------------------
// 返回指定文本是否以指定文本引导或者终止

inline_ BOOL_P LeadOf (const _MYS_TCHAR* szTest, const _MYS_TCHAR chLeadOf)
{
    ASSERT_R_STR (szTest);
    return (*szTest == chLeadOf);
}

inline_ BOOL_P LeadOf (const _MYS_TCHAR* szTest, const _MYS_TCHAR* szLeadOf, const INT_P npLeaderTextLength)
{
    ASSERT_R_STR (szTest);
    ASSERT_R_STR (szLeadOf);
    ASSERT (npLeaderTextLength >= 0);

    return (_MYS_STRNCMP (szTest, szLeadOf, npLeaderTextLength) == 0);
}

inline_ BOOL_P LeadOf (const _MYS_TCHAR* szTest, const _MYS_TCHAR* szLeadOf)
{
    ASSERT_R_STR (szTest);
    ASSERT_R_STR (szLeadOf);

    return (_MYS_STRNCMP (szTest, szLeadOf, _MYS_STRLEN (szLeadOf)) == 0);
}

inline_ BOOL_P ILeadOf (const _MYS_TCHAR* szTest, const _MYS_TCHAR chLeadOf)
{
    ASSERT_R_STR (szTest);

    return (TO_UPPER_CASE (*szTest) == TO_UPPER_CASE (chLeadOf));
}

inline_ BOOL_P ILeadOf (const _MYS_TCHAR* szTest, const _MYS_TCHAR* szLeadOf, const INT_P npLeaderTextLength)
{
    ASSERT_R_STR (szTest);
    ASSERT_R_STR (szLeadOf);
    ASSERT (npLeaderTextLength >= 0);

    return (_MYS_STRNICMP (szTest, szLeadOf, npLeaderTextLength) == 0);
}

inline_ BOOL_P ILeadOf (const _MYS_TCHAR* szTest, const _MYS_TCHAR* szLeadOf)
{
    ASSERT_R_STR (szTest);
    ASSERT_R_STR (szLeadOf);

    return (_MYS_STRNICMP (szTest, szLeadOf, _MYS_STRLEN (szLeadOf)) == 0);
}

inline_ BOOL_P EndOf (const _MYS_TCHAR* szTest, const _MYS_TCHAR chEndOf)
{
    ASSERT_R_STR (szTest);

    const INT_P npTestStrLen = _MYS_STRLEN (szTest);
    return (npTestStrLen > 0 && szTest [npTestStrLen - 1] == chEndOf);
}

BOOL_P EndOf (const _MYS_TCHAR* szTest, const _MYS_TCHAR* szEndOf);
BOOL_P IEndOf (const _MYS_TCHAR* szTest, const _MYS_TCHAR* szEndOf);

// 跳过所有空白字符,返回跳过空白字符后的文本指针.
//   ps: 欲处理的文本指针
const _MYS_TCHAR* SkipSpaces (const _MYS_TCHAR* ps);
//   psEndMark: 文本的结束指针(*psEndMark字符本身不包括在内)
const _MYS_TCHAR* SkipSpaces (const _MYS_TCHAR* ps, const _MYS_TCHAR* psEndMark);

// 反向跳过所有空白字符,返回首空白字符的前一字符指针(注意可能等于psBegin-1).
// 如果ps小于psBegin,则直接返回ps.
const _MYS_TCHAR* RSkipSpaces (const _MYS_TCHAR* ps, const _MYS_TCHAR* psBegin);

//--------------------------------------------------  文本/数值转换

// 将指定整数值转换为文本存放到psResult中并将其返回
// psResult必须指向足够空间长度的缓冲区,至少为32个字符空间.
inline_ const _MYS_TCHAR* n2str (const INT nValue, _MYS_TCHAR* psResult)
{
    ASSERT_RW_ADR (psResult, 32 * sizeof (_MYS_TCHAR));

#ifdef _PF_WINDOWS
    #ifdef _MY_WSTRING_IMPL
        return _itow (nValue, psResult, 10);
    #else
        return _itoa (nValue, psResult, 10);
    #endif
#else
    _stprintf (psResult, _MYS_T ("%d"), nValue);
    return psResult;
#endif
}

// 返回指定文本转换到整数后的结果
inline_ INT_P str2n (const _MYS_TCHAR* szText)
{
    ASSERT_R_STR (szText);
    return _MYS_TTOI (szText);
}

// 返回指定十六进制字符转换到整数后的结果,无效返回-1.
INT_P HexCharToValue (const _MYS_TCHAR chHexChar);

// 将upByte字节转换为2个十六进制字符并存放到psTwoChars处.
//   upByte: 待转换的字节值
//   psTwoChars: 指向具有2个字符存放空间的地址
void Byte2TwoHexChars (const UINT_P upByte, _MYS_TCHAR* psTwoChars);

// 返回指定十六进制文本转换到无符号整数后的结果
UINT_P Hex2UP (const _MYS_TCHAR* szHexText);
UINT64 Hex2U64 (const _MYS_TCHAR* szHexText);

// 将指定数值转换为十六进制文本并返回
//   npReqMinWidth: 所需求的最小宽度(数字数目),如果有效数值宽度小于该值,则自动在首部加0. 为0表示去除所有的前置'0'数字.
//   psBuf必须指向足够空间长度的缓冲区,推荐至少为17个字符空间.
//   npBufLength提供缓冲区的以字符为单位的尺寸,如果此尺寸过小则返回空文本.
template <typename T>
const _MYS_TCHAR* ToHexStr (const T number, INT_P npReqMinWidth, _MYS_TCHAR* psBuf, const INT_P npBufLength)
{
    if (npBufLength < (INT_P)sizeof (T) * 8 / 4 + 1)  // 此为缓冲区最小需求尺寸
    {
        FAIL;
        return _MYS_T ("");
    }
    ASSERT_RW_ADR (psBuf, npBufLength * sizeof (_MYS_TCHAR));

    _MYS_TCHAR buf [32];
    _MYS_TCHAR* ps = buf;
    const _MYS_TCHAR* psFirstNotZero = NULL;  // 用作记录首个非'0'字符,为NULL表示全部为'0'.

    INT_P npShiftBits = sizeof (T) * 8 - 4;
    ASSERT (npShiftBits >= 4);  // T最少也是1字节
    for (INT_P npIndex = 0; npIndex < (INT_P)sizeof (T) * 8 / 4; npIndex++)
    {
        const static _MYS_TCHAR cs_hex [] =
        {
            '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F'
        };
        COMPILE_TIME_ASSERT (NUM_ELEMENTS_OF (cs_hex) == 16);

        // 获得对应的字符索引
        const INT_P npCharIndex = (INT_P)((number >> npShiftBits) & 0x0F);

        // 记录第一个非'0'字符位置
        if (psFirstNotZero == NULL && npCharIndex != 0)
            psFirstNotZero = ps;

        *ps++ = cs_hex [npCharIndex];
        npShiftBits -= 4;
    }

    ASSERT (npShiftBits == -4 && ps == buf + sizeof (T) * 8 / 4);
    *ps = '\0';

    const _MYS_TCHAR* szResult;
    if (npReqMinWidth > 0)  // 设定了最小需求宽度?
    {
        ps -= npReqMinWidth;

        if (ps < buf)
        {
            szResult = buf;
        }
        else if (psFirstNotZero == NULL)
        {
            ASSERT (number == 0);  // 必定为0
            szResult = ps;
        }
        else
            szResult = MIN (psFirstNotZero, ps);
    }
    else
    {
        if (psFirstNotZero == NULL)
        {
            ASSERT (number == 0);  // 必定为0
            szResult = _MYS_T ("0");
        }
        else
            szResult = psFirstNotZero;  // 跳过前面所有的'0'字符
    }

    _MYS_STRCPY (psBuf, szResult);
    return psBuf;
}

inline_ const _MYS_TCHAR* UPToHexStr (const UINT_P up, const INT_P npReqMinWidth, _MYS_TCHAR* psBuf, const INT_P npBufLength)
{
    return ToHexStr (up, npReqMinWidth, psBuf, npBufLength);
}
inline_ const _MYS_TCHAR* U64ToHexStr (const UINT64 u64, const INT_P npReqMinWidth, _MYS_TCHAR* psBuf, const INT_P npBufLength)
{
    return ToHexStr (u64, npReqMinWidth, psBuf, npBufLength);
}
inline_ const _MYS_TCHAR* DWordToHexStr (const DWORD dw, const INT_P npReqMinWidth, _MYS_TCHAR* psBuf, const INT_P npBufLength)
{
    return ToHexStr (dw, npReqMinWidth, psBuf, npBufLength);
}
inline_ const _MYS_TCHAR* WordToHexStr (const WORD w, const INT_P npReqMinWidth, _MYS_TCHAR* psBuf, const INT_P npBufLength)
{
    return ToHexStr (w, npReqMinWidth, psBuf, npBufLength);
}
inline_ const _MYS_TCHAR* ByteToHexStr (const BYTE bt, const INT_P npReqMinWidth, _MYS_TCHAR* psBuf, const INT_P npBufLength)
{
    return ToHexStr (bt, npReqMinWidth, psBuf, npBufLength);
}

// 将指定64位整数值转换为文本并将其返回
// psBuf必须指向足够空间长度的缓冲区,至少为32个字符空间
// npBufLength提供缓冲区的以字符为单位的尺寸,如果此尺寸过小则返回空文本.
const _MYS_TCHAR* N64ToStr (INT64 n64, _MYS_TCHAR* psBuf, const INT_P npBufLength);

// 将指定10进制文本转换为INT64整数类型并返回
INT64 StrToN64 (const _MYS_TCHAR* ps);

// 返回ps是否能被转换到INT或INT64整数
BOOL_P CheckInteger (const _MYS_TCHAR* ps);

// 返回ps是否能被转换到DWORD或UINT64无符号整数
BOOL_P CheckUnsignInteger (const _MYS_TCHAR* ps);

// 返回ps是否能被转换到DWORD或UINT64无符号十六进制整数
BOOL_P CheckHexInteger (const _MYS_TCHAR* ps);

// 将ps转换到整数,保存到*pnpResult中,如果ps文本格式出错,返回假,否则返回真.
// 支持以"0x"开头的十六进制格式.
BOOL_P Str2IntCheck (const _MYS_TCHAR* ps, INT_P* pnpResult);

// 将ps转换到长整数,保存到*pn64Result中,如果ps文本格式出错,返回假,否则返回真.
// 支持以"0x"开头的十六进制格式.
//   pblpIsHexNumber: 如果不为NULL,则在其中记录是否为16进制整数.
BOOL_P Str2Int64Check (const _MYS_TCHAR* ps, INT64* pn64Result, BOOL_P* pblpIsHexNumber);

// 将ps转换到双精度小数,保存到*pdbResult中,如果ps文本格式出错,返回假,否则返回真.
BOOL_P Str2DoubleCheck (const _MYS_TCHAR* ps, DOUBLE* pdbResult);

// 将ps转换到小数,保存到*pfResult中,如果ps文本格式出错,返回假,否则返回真.
BOOL_P Str2FloatCheck (const _MYS_TCHAR* ps, FLOAT* pfResult);

// 返回ps是否能被转换到DOUBLE
inline_ BOOL_P CheckDouble (const _MYS_TCHAR* ps)
{
    DOUBLE db;
    return Str2DoubleCheck (ps, &db);
}

// 将指定的UINT_P整数值转换为文本并将其返回
// psResult必须指向足够空间长度的缓冲区,至少为32个字符空间.
inline_ const _MYS_TCHAR* up2str (const UINT_P upValue, _MYS_TCHAR* psResult)
{
    ASSERT_RW_ADR (psResult, 32 * sizeof (_MYS_TCHAR));

#ifdef _PF_64_BITS  // 64位目标平台?
    _MYS_SPRINTF (psResult, _MYS_T ("%I64u"), upValue);
#else
    _MYS_SPRINTF (psResult, _MYS_T ("%u"), upValue);
#endif
    return psResult;
}

// 将指定整数值转换为文本存放到psResult中并将其返回
// psResult必须指向足够空间长度的缓冲区,至少为32个字符空间.
inline_ const _MYS_TCHAR* np2str (const INT_P npValue, _MYS_TCHAR* psResult)
{
    ASSERT_RW_ADR (psResult, 32 * sizeof (_MYS_TCHAR));

#ifdef _PF_32_BITS
    return n2str (npValue, psResult);
#else
    return N64ToStr ((INT64)npValue, psResult, 32);
#endif
}

inline_ INT_P str2np (const _MYS_TCHAR* szText)
{
    ASSERT_R_STR (szText);

#ifdef _PF_32_BITS
    return _MYS_TTOI (szText);
#else
    return StrToN64 (szText);
#endif
}

//--------------------------------------------------  其它

void ConvertToLowerText (_MYS_TCHAR* ps);  // 将ps文本串中的大写字母转换为小写
void ConvertToUpperText (_MYS_TCHAR* ps);  // 将ps文本串中的小写字母转换为大写

// 在文本内容中搜寻返回第一个匹配指定文本的位置指针,未找到返回NULL.
//   psText: 被搜寻文本内容
//   npTextLength: 被搜寻文本内容的长度,为-1表示搜寻整个文本.
//   psFindText: 用来搜寻的文本
//   npFindTextLength: 用来搜寻文本的长度,为-1表示搜寻整个文本.
//   blpCaseInsensitive: 是否字母大小写无关
const _MYS_TCHAR* FindString (const _MYS_TCHAR* psText, INT_P npTextLength, const _MYS_TCHAR* psFindText,
        INT_P npFindTextLength, const BOOL_P blpCaseInsensitive, const BOOL_P blpReverseFind);

//--------------------------------------------------  支持快速比较的常量文本类

// 不忽略大小写的快速常量文本比较类
class _Q_COMPARE_CONST_TEXT
{
public:
    // 注意szStaticText必须是字符串常量文本
    inline_ _Q_COMPARE_CONST_TEXT (const _MYS_TCHAR* szStaticText)
    {
        ASSERT_R_STR_OR_NULL (szStaticText);

        m_szStaticText = (szStaticText == NULL ? _MYS_T ("") : szStaticText);
        m_dwTextHash = GetTextHash (m_szStaticText, &m_npTextLength);
    }

    inline_ _Q_COMPARE_CONST_TEXT (const _Q_COMPARE_CONST_TEXT& text)
    {
        m_szStaticText = text.m_szStaticText;
        m_npTextLength = text.m_npTextLength;
        m_dwTextHash = text.m_dwTextHash;
    }

public:
    inline_ BOOL_P IsEmpty () const
    {
        return (m_npTextLength == 0);
    }

    inline_ const _MYS_TCHAR* GetStaticText () const
    {
        return m_szStaticText;
    }

    inline_ INT_P GetStaticTextLength () const
    {
        return m_npTextLength;
    }

    inline_ DWORD GetStaticTextHash () const
    {
        return m_dwTextHash;
    }

    inline_ BOOL_P IsEqual (const _MYS_TCHAR* szText) const
    {
        ASSERT_R_STR (szText);
        return (_MYS_STRCMP (szText, m_szStaticText) == 0);
    }

    inline_ BOOL_P IsEqual (const _MYS_TCHAR* szText, const DWORD dwTextHash) const
    {
        ASSERT_R_STR (szText);
        return (dwTextHash == m_dwTextHash && _MYS_STRCMP (szText, m_szStaticText) == 0);
    }

    inline_ BOOL_P IsEqual (const _MYS_TCHAR* psText, const INT_P npTextLength, const DWORD dwTextHash) const
    {
        ASSERT_R_STR2 (psText, npTextLength);
        return (dwTextHash == m_dwTextHash && npTextLength == m_npTextLength &&
                _MYS_STRNCMP (psText, m_szStaticText, npTextLength) == 0);
    }

    inline_ BOOL_P IsEqualWithoutHash (const _MYS_TCHAR* psText, const INT_P npTextLength) const
    {
        ASSERT_R_STR2 (psText, npTextLength);
        return (npTextLength == m_npTextLength &&
                _MYS_STRNCMP (psText, m_szStaticText, npTextLength) == 0);
    }

    inline_ BOOL_P IsEqual (const _Q_COMPARE_CONST_TEXT& text) const
    {
        return (text.m_dwTextHash == m_dwTextHash && text.m_npTextLength == m_npTextLength &&
                _MYS_STRNCMP (text.m_szStaticText, m_szStaticText, m_npTextLength) == 0);
    }

protected:
    const _MYS_TCHAR* m_szStaticText;
    INT_P m_npTextLength;
    DWORD m_dwTextHash;
};

//----------------------------------------------------------------------------------

// 忽略大小写的快速常量文本比较类
class _Q_COMPARE_I_CONST_TEXT
{
public:
    // 注意szStaticText必须是字符串常量文本
    inline_ _Q_COMPARE_I_CONST_TEXT (const _MYS_TCHAR* szStaticText)
    {
        ASSERT_R_STR_OR_NULL (szStaticText);

        m_szStaticText = (szStaticText == NULL ? _MYS_T ("") : szStaticText);
        m_dwTextIHash = GetTextIHash (m_szStaticText, &m_npTextLength);
    }

    inline_ _Q_COMPARE_I_CONST_TEXT (const _Q_COMPARE_I_CONST_TEXT& text)
    {
        m_szStaticText = text.m_szStaticText;
        m_npTextLength = text.m_npTextLength;
        m_dwTextIHash = text.m_dwTextIHash;
    }

public:
    inline_ BOOL_P IsEmpty () const
    {
        return (m_npTextLength == 0);
    }

    inline_ const _MYS_TCHAR* GetStaticText () const
    {
        return m_szStaticText;
    }

    inline_ INT_P GetStaticTextLength () const
    {
        return m_npTextLength;
    }

    inline_ DWORD GetStaticTextIHash () const
    {
        return m_dwTextIHash;
    }

    inline_ BOOL_P IsEqual (const _MYS_TCHAR* szText) const
    {
        ASSERT_R_STR (szText);
        return (_MYS_STRICMP (szText, m_szStaticText) == 0);
    }

    inline_ BOOL_P IsEqual (const _MYS_TCHAR* szText, const DWORD dwTextIHash) const
    {
        ASSERT_R_STR (szText);
        return (dwTextIHash == m_dwTextIHash && _MYS_STRICMP (szText, m_szStaticText) == 0);
    }

    inline_ BOOL_P IsEqual (const _MYS_TCHAR* psText, const INT_P npTextLength, const DWORD dwTextIHash) const
    {
        ASSERT_R_STR2 (psText, npTextLength);
        return (dwTextIHash == m_dwTextIHash && npTextLength == m_npTextLength &&
                _MYS_STRNICMP (psText, m_szStaticText, npTextLength) == 0);
    }

    inline_ BOOL_P IsEqualWithoutHash (const _MYS_TCHAR* psText, const INT_P npTextLength) const
    {
        ASSERT_R_STR2 (psText, npTextLength);
        return (npTextLength == m_npTextLength &&
                _MYS_STRNICMP (psText, m_szStaticText, npTextLength) == 0);
    }

    inline_ BOOL_P IsEqual (const _Q_COMPARE_I_CONST_TEXT& text) const
    {
        return (text.m_dwTextIHash == m_dwTextIHash && text.m_npTextLength == m_npTextLength &&
                _MYS_STRNICMP (text.m_szStaticText, m_szStaticText, m_npTextLength) == 0);
    }

protected:
    const _MYS_TCHAR* m_szStaticText;
    INT_P m_npTextLength;
    DWORD m_dwTextIHash;
};
