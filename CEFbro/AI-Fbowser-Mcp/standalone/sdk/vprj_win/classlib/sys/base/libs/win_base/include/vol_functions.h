
// Copyright (C) Recursion Company. All rights reserved.

#ifndef __VOL_FUNCTIONS_H__
#define __VOL_FUNCTIONS_H__

class CVolMem;
class CVolString;
class CMStringArray;
template <class T> class CMArray;

//-----------------------------------------------  内存的可访问性校验

#ifdef _PF_WINDOWS

// 返回psz所指向的以'\0'结束的字符串地址空间是否有效可读取
inline_ BOOL_P IsValidString (const WCHAR* pwsz)
{
    return (pwsz != NULL && IsBadStringPtrW (pwsz, (UINT_PTR)INT_MAX) == FALSE);
}
inline_ BOOL_P IsValidString (const U8CHAR* psz)
{
    return (psz != NULL && IsBadStringPtrA (psz, (UINT_PTR)INT_MAX) == FALSE);
}

// 返回p所指向的nBytes尺寸的地址空间是否有效可访问
//   blpReadWrite: 为假只检查是否可读,否则检查是否可读写.
BOOL_P IsValidAddress (const void* p, const INT_P npSize, const BOOL_P blpReadWrite);

// 返回pData所指向的数据地址空间是否有效可访问
//   blpReadWrite: 为假只检查是否可读,否则检查是否可读写.
template<typename T> inline_ BOOL_P IsValidDataPointer (const T* pData, const BOOL_P blpReadWrite)
{
    return IsValidAddress (pData, sizeof (T), blpReadWrite);
}

// 返回指定文本指针所指向的长度为npLength的字符串地址空间是否有效可读取
//   npLength: 所检查的字符数目,必须大于等于0.
inline_ BOOL_P IsValidString (const WCHAR* pwsz, const INT_P npLength)
{
    ASSERT (npLength >= 0);
    return IsValidAddress (pwsz, sizeof (WCHAR) * npLength, FALSE);
}
inline_ BOOL_P IsValidString (const U8CHAR* psz, const INT_P npLength)
{
    ASSERT (npLength >= 0);
    return IsValidAddress (psz, sizeof (U8CHAR) * npLength, FALSE);
}
//   npLength: 所检查的字符数目,必须大于等于-1,为-1表示一直检查到该文本的零字符处.
inline_ BOOL_P IsValidStringSupportLenNeg1 (const WCHAR* pwsz, const INT_P npLength)
{
    ASSERT (npLength >= -1);
    return (npLength < 0 ? IsValidString (pwsz) : IsValidAddress (pwsz, sizeof (WCHAR) * npLength, FALSE));
}
inline_ BOOL_P IsValidStringSupportLenNeg1 (const U8CHAR* psz, const INT_P npLength)
{
    ASSERT (npLength >= -1);
    return (npLength < 0 ? IsValidString (psz) : IsValidAddress (psz, sizeof (U8CHAR) * npLength, FALSE));
}

#endif

//-----------------------------------------------  浮点数操作

// 判断指定浮点数是否为0
inline_ BOOL_P IsFloatEqualZero (const FLOAT f)
{
    return (f >= -NEAR_ZERO_FLOAT && f <= NEAR_ZERO_FLOAT);
}
inline_ BOOL_P IsDoubleEqualZero (const DOUBLE db)
{
    return (db >= -NEAR_ZERO_DOUBLE && db <= NEAR_ZERO_DOUBLE);
}
inline_ BOOL_P IsFloatEqualZero (const FLOAT f, const FLOAT fEpsilon)
{
    return (f >= -fEpsilon && f <= fEpsilon);
}
inline_ BOOL_P IsDoubleEqualZero (const DOUBLE db, const DOUBLE dbEpsilon)
{
    return (db >= -dbEpsilon && db <= dbEpsilon);
}

// 返回两个浮点数是否相等
inline_ BOOL_P _NAME_COMPILER_AGREED (IsFloatEqual) (const FLOAT f1, const FLOAT f2)
{
    return IsFloatEqualZero (f1 - f2);
}
inline_ BOOL_P _NAME_COMPILER_AGREED (IsDoubleEqual) (const DOUBLE db1, const DOUBLE db2)
{
    return IsDoubleEqualZero (db1 - db2);
}
inline_ BOOL_P IsFloatEqual (const FLOAT f1, const FLOAT f2, const FLOAT fEpsilon)
{
    return IsFloatEqualZero (f1 - f2, fEpsilon);
}
inline_ BOOL_P IsDoubleEqual (const DOUBLE db1, const DOUBLE db2, const DOUBLE dbEpsilon)
{
    return IsDoubleEqualZero (db1 - db2, dbEpsilon);
}

inline_ INT_P IntPMulDouble (const INT_P npValue, const DOUBLE db)
{
    return (INT_P)((DOUBLE)npValue * db + 0.5);
}
inline_ INT IntMulDouble (const INT nValue, const DOUBLE db)
{
    return (INT)((DOUBLE)nValue * db + 0.5);
}

inline_ INT_P IntPDivDouble (const INT_P npValue, const DOUBLE db)
{
    return (INT_P)((DOUBLE)npValue / db + 0.5);
}
inline_ INT IntDivDouble (const INT nValue, const DOUBLE db)
{
    return (INT)((DOUBLE)nValue / db + 0.5);
}

//-----------------------------------------------  文本操作

// 返回所指定文本指针是否为NULL或者空文本
inline_ BOOL_P _NAME_COMPILER_AGREED (IsEmptyStr) (const WCHAR* wszText)
{
    ASSERT_R_STR_OR_NULL (wszText);
    return (wszText == NULL || *wszText == '\0');
}
inline_ BOOL_P _NAME_COMPILER_AGREED (IsEmptyStr) (const U8CHAR* szText)
{
    ASSERT_R_STR_OR_NULL (szText);
    return (szText == NULL || *szText == '\0');
}

// 与strncpy/wcsncpy唯一不同的地方是必定会附加一个'\0'结束字符
void strncpy_z (U8CHAR* dest, const U8CHAR* source, const INT_P npNumChars);
void wcsncpy_z (WCHAR* dest, const WCHAR* source, const INT_P npNumChars);

// 与_tcsncpy唯一不同的地方是必定会附加一个'\0'结束字符
#ifdef _UNICODE
    #define _tcsncpy_z  wcsncpy_z
#else
    #define _tcsncpy_z  strncpy_z
#endif

// 将szText文本根据chDelimit字符进行分割,分割结果存放到所提供的数组变量中.
//   blpTrimAll: 所分割出来的文本是否去除首尾空白
//   blpIgnoreEmptyStr: 是否忽略空白文本
INT_P SplitStrings (const TCHAR* szText, CMStringArray& strary, const TCHAR chDelimit, const BOOL_P blpTrimAll, const BOOL_P blpIgnoreEmptyStr);
INT_P SplitIntegers (const TCHAR* szText, CMArray<INT>& nary, const TCHAR chDelimit);
INT_P SplitDoubles (const TCHAR* szText, CMArray<DOUBLE>& dbary, const TCHAR chDelimit);

// 把文本根据所指定字符首次出现的位置分割成左右两个部分,分割成功返回真,未找到所指定的分割字符返回假.
BOOL_P SplitString2 (const TCHAR* szText, const TCHAR chDelimit, const BOOL_P blpTrimAll, CVolString& strLeft, CVolString& strRight);

// 把文本根据所指定子文本首次出现的位置分割成左右两个部分,分割成功返回真,未找到所指定的分割字符返回假.
BOOL_P SplitSubString2 (const TCHAR* szText, const TCHAR* szDelimitText, const BOOL_P blpTrimAll, CVolString& strLeft, CVolString& strRight);

// 将szText文本根据szDelimit文本中列出的每个字符进行分割,分割结果存放到所提供的数组变量中.
//   szDelimit: 该文本中的每个字符均被认为是分隔符
//   blpTrimAll: 所分割出来的文本是否去除首尾空白
//   blpIgnoreEmptyStr: 是否忽略空白文本
INT_P SplitStringsSupportManyDelimitChar (const TCHAR* szText, CMStringArray& strary, const TCHAR* szDelimit,
        const BOOL_P blpTrimAll, const BOOL_P blpIgnoreEmptyStr);

// 将szText文本根据szDelimitText子文本进行分割,分割结果存放到所提供的数组变量中.
//   szDelimitText: 分割用的子文本
//   blpTrimAll: 所分割出来的文本是否去除首尾空白
//   blpIgnoreEmptyStr: 是否忽略空白文本
INT_P SplitSubStrings (const TCHAR* szText, CMStringArray& strary, const TCHAR* szDelimitText, const BOOL_P blpTrimAll, const BOOL_P blpIgnoreEmptyStr);

// 将strary中的所有文本使用chDelimit字符分隔后组合到一起存放到strResult中并返回
//   blpInsertSpace: 是否在chDelimit字符后插入一个空白字符
const TCHAR* ComboStrings (const CMStringArray& strary, CVolString& strResult, const TCHAR chDelimit, const BOOL_P blpInsertSpace);

// 返回长度为npTextLength的psText文本中chTest字符的数目,chTest不能为'\0'.
INT_P CounterChar (const TCHAR* psText, const INT_P npTextLength, const TCHAR chTest);
inline_ INT_P CounterChar (const TCHAR* szText, const TCHAR chTest)
{
    ASSERT_R_STR (szText);
    return (IsEmptyStr (szText) ? 0 : CounterChar (szText, _tcslen (szText), chTest));
}

// 将所指定的数值转换为简体或繁体的大写形式
//   dbNumber: 所欲转换的数值,其小数位被舍入到两位.
//   blpConvertToSimple: 为真转换为简体,为假则转换为繁体.
//   strConvertResult: 存放转换结果
void NumberToCNText (DOUBLE dbNumber, const BOOL_P blpConvertToSimple, CVolString& strConvertResult);
// 将所指定的数值转换为简体或繁体的大写货币形式
void NumberToCurrency (DOUBLE dbNumber, const BOOL_P blpConvertToSimple, CVolString& strConvertResult);
// 将所指定的数值转换为指定格式的文本
//   npFracKeepNumber: 小数保留位数
//   blpTausendstelSeparation: 是否进行千分位分隔
void NumberToFormatText (DOUBLE dbNumber, const INT_P npFracKeepNumber, const BOOL_P blpTausendstelSeparation, CVolString& strConvertResult);

//----------------------------------------------- 文本转换

// Unicode -> UTF8
U8CHAR* ConvertText (const WCHAR* wszText, const INT_P npLen, CVolMem& memBuf);
inline_ U8CHAR* ConvertText (const WCHAR* wszText, CVolMem& memBuf)
{
    return ConvertText (wszText, wcslen (wszText), memBuf);
}

// UTF8 -> Unicode
WCHAR* ConvertText (const U8CHAR* szText, const INT_P npLen, CVolMem& memBuf);
inline_ WCHAR* ConvertText (const U8CHAR* szText, CVolMem& memBuf)
{
    return ConvertText (szText, strlen (szText), memBuf);
}

//-----------------------------------------------  字符编码处理

// 将指定宽字符文本转换为utf8文本并存放到memBuf中,返回转换后的utf8文本指针.
//   npLength: 提供pwsText文本的长度,如果为-1,则自行计算.
//   pnpUtf8StrLength: 如果不为NULL,则在其中返回转换后utf8文本的字符数(不包括结束'\0'字符).
//   pblpFoundInvalidChar: 如果不为NULL,则在其中返回pwsText中是否存在无效Unicode字符.
//   blpCutBufSpace: 是否切除缓冲区尾部的多余空间
U8CHAR* WStrToUtf8 (const WCHAR* pwsText, INT_P npLength, CVolMem& memBuf, INT_P* pnpUtf8StrLength = NULL,
        BOOL_P* pblpFoundInvalidChar = NULL, const BOOL_P blpCutBufSpace = FALSE);

// 返回指定UTF8字符的字节数,如果无效则返回-1.
INT_P GetUTF8CharBytes (const BYTE btU8CharLeader);

// 将指定utf8字符文本转换为宽字符文本并存放到memBuf中,返回转换后的宽字符文本指针.
//   npLength: 提供psText文本的长度,如果为-1,则自行计算.
//   pnpWStrLength: 如果不为NULL,则在其中返回转换后宽字符文本的字符数(不包括结束'\0'字符).
//   pblpFoundInvalidChar: 如果不为NULL,则在其中返回psText中是否存在无效Unicode字符.
//   blpCutBufSpace: 是否切除缓冲区尾部的多余空间
WCHAR* Utf8ToWStr (const U8CHAR* psText, INT_P npLength, CVolMem& memBuf, INT_P* pnpWStrLength = NULL,
        BOOL_P* pblpFoundInvalidChar = NULL, const BOOL_P blpCutBufSpace = FALSE);

// 返回指定utf8文本的字符数目,如果存在无效字符,则返回-1.
INT_P GetU8StrLength (const U8CHAR* psText);

// 返回指定utf8文本中给是否不存在任何无效的utf8字符
inline_ BOOL_P IsValidU8Str (const U8CHAR* psText)
{
    return (GetU8StrLength (psText) != -1);
}

// 返回psCurrent的前一个utf8字符指针,如果psCurrent已经位于文本首部或其前一字符无效则返回NULL.
//   psCurrent:   当前字符的文本指针. 注意: 不需要psCurrent一定指向某个utf8字符的首字节处,位于中间位置也可,
//              也就是说,psCurrent可以指向utf8文本字符串中的任何位置.
//   psTextBegin: 文本起始位置指针
// 注意,本方法中的无效字符判断并不全面,如果需要全面判断需要调用GetU8StrLength/IsValidU8Str.
U8CHAR* PrevU8Char (U8CHAR* psCurrent, const U8CHAR* psTextBegin);

// 返回psCurrent的后一个utf8字符指针,如果psCurrent已经位于文本尾部或所指向字符无效则返回NULL.
//   psCurrent:   当前字符的文本指针. 注意: 不需要psCurrent一定指向某个utf8字符的首字节处,位于中间位置也可,
//              也就是说,psCurrent可以指向utf8文本字符串中的任何位置.
// 注意,本方法中的无效字符判断并不全面,如果需要全面判断需要调用GetU8StrLength/IsValidU8Str.
U8CHAR* NextU8Char (U8CHAR* psCurrent);

// 将所指定宽文本转换到本地多字节文本
//   pnpResultTextLength: 如果不为NULL,则在其中返回所转换后的文本数据的字符数目(不包括结束零).
const CHAR* GetMbsText (const WCHAR* szText, CVolMem& memBuf, INT_P* pnpResultTextLength);

// 将所指定本地多字节文本转换到宽文本
//   pnpResultTextLength: 如果不为NULL,则在其中返回所转换后的文本数据的字符数目(不包括结束零).
const WCHAR* GetWideText (const CHAR* szText, CVolMem& memBuf, INT_P* pnpResultTextLength);

//------------------------------------------------------------------

// 返回psText去除了尾部空白字符后的长度
//   psEndMark: 文本的结束指针(*psEndMark字符本身不包括在内)
INT_P GetTextLengthWithoutTailSpaces (const TCHAR* psText, const TCHAR* psEndMark);
inline_ INT_P GetTextLengthWithoutTailSpaces (const TCHAR* szText)
{
    ASSERT_R_STR (szText);
    return GetTextLengthWithoutTailSpaces (szText, szText + _tcslen (szText));
}

// 将psText文本去除首尾空白,返回跳过首部空白后的文本指针.
//   psEndMark: 文本的结束指针(*psEndMark字符本身不包括在内)
//   pnpLength: 如果不为NULL,则在其中返回去除首尾空白后的文本长度.
const TCHAR* TextTrimAll (const TCHAR* psText, const TCHAR* psEndMark, INT_P* pnpLength);
inline_ const TCHAR* TextTrimAll (const TCHAR* szText, INT_P* pnpLength)
{
    ASSERT_R_STR (szText);
    return TextTrimAll (szText, szText + _tcslen (szText), pnpLength);
}

// 将所指定文本转换为对应的逻辑值,返回所指定文本格式是否符合要求.
//   szValueText: 所欲转换的文本: "真"/"true"(不区分大小写)/"1"被转换为逻辑值真,"假"/"false"(不区分大小写)/"0"被转换为逻辑值假.
//   pblpValue: 如果不为NULL,则在其中填入所转换到的逻辑值(转换失败亦填入默认的逻辑值假).
BOOL_P IsBoolValueText (const TCHAR* szValueText, BOOL_P* pblpValue);
// 直接返回szValueText所对应的逻辑值,如果其格式不符合要求,则返回默认逻辑值假.
inline_ BOOL_P StrToBool (const TCHAR* szValueText)
{
    BOOL_P blpValue;
    IsBoolValueText (szValueText, &blpValue);
    return blpValue;
}

// 在指定文本中寻找所指定子文本. 找到返回文本指针,未找到返回NULL.
//   psCurrent: 该文本到psEndMark(*psEndMark字符本身不包括在内)指定了欲搜寻文本段.
//   szFindText: 欲查找子文本
//   blpIgnoreCase: 比较时是否忽略大小写
const TCHAR* FindSubString (const TCHAR* psCurrent, const TCHAR* psEndMark, const TCHAR* szFindText, const BOOL_P blpIgnoreCase);
inline_ const TCHAR* FindSubString (const TCHAR* psCurrent, const TCHAR* szFindText, const BOOL_P blpIgnoreCase)
{
    ASSERT_R_STR (psCurrent);
    return FindSubString (psCurrent, psCurrent + _tcslen (psCurrent), szFindText, blpIgnoreCase);
}

// 替换指定文本中的所有指定子文本,返回替换后的结果.
//   psFind: 该文本到psEndMark(*psEndMark字符本身不包括在内)指定了欲搜寻文本段.
//   szNeedReplaceText: 提供欲替换文本
//   szReplaceToText: 提供替换到的文本
//   blpIgnoreCase: 比较时是否忽略大小写
//   strReplaceResult: 用作保存替换结果
// 返回存放到strReplaceResult中的替换结果文本
const TCHAR* ReplaceSubString (const TCHAR* psFind, const TCHAR* psEndMark, const TCHAR* szNeedReplaceText,
        const TCHAR* szReplaceToText, const BOOL_P blpIgnoreCase, CVolString& strReplaceResult);
inline_ const TCHAR* ReplaceSubString (const TCHAR* szFind, const TCHAR* szNeedReplaceText,
        const TCHAR* szReplaceToText, const BOOL_P blpIgnoreCase, CVolString& strReplaceResult)
{
    ASSERT_R_STR (szFind);
    return ReplaceSubString (szFind, szFind + _tcslen (szFind),
            szNeedReplaceText, szReplaceToText, blpIgnoreCase, strReplaceResult);
}

// 获取psText处的一个字符,将其填入到*pchResult中,并返回下一个字符指针. 支持转义字符.
//   psEndMark: 文本的结束指针(*psEndMark字符本身不包括在内);
//   pchResult: 用作保存结果字符,不能为NULL.
const TCHAR* GetEscapeChar (const TCHAR* psText, const TCHAR* psEndMark, TCHAR* pchResult);
inline_ const TCHAR* GetEscapeChar (const TCHAR* szText, TCHAR* pchResult)
{
    return GetEscapeChar (szText, szText + _tcslen (szText), pchResult);
}

// 处理psText到psEndMark之间文本中的所有转义字符,返回处理后的结果文本.
//   psEndMark: 文本的结束指针(*psEndMark字符本身不包括在内);
const TCHAR* EscapeToPlainText (const TCHAR* psText, const TCHAR* psEndMark, CVolMem& memBuf);
inline_ const TCHAR* EscapeToPlainText (const TCHAR* szText, CVolMem& memBuf)
{
    return EscapeToPlainText (szText, szText + _tcslen (szText), memBuf);
}

// 处理psText到psEndMark之间文本中的所有字符,将其中的所有不可视字符转换为转义字符后返回.
//   psEndMark: 文本的结束指针(*psEndMark字符本身不包括在内);
// 本方法的返回文本格式c/c++/java均支持.
const TCHAR* PlainToEscapeText (const TCHAR* psText, const TCHAR* psEndMark, CVolMem& memBuf);
inline_ const TCHAR* PlainToEscapeText (const TCHAR* szText, CVolMem& memBuf)
{
    return PlainToEscapeText (szText, szText + _tcslen (szText), memBuf);
}

// 将szPlainText转换为字符串格式(将其中的所有不可视字符转换为转义字符),然后填入到*pstrResult中返回.
//   blpEncloseEmptyStr: 指定当文本为空时,是否也用双引号将其括住而不直接返回空文本.
const TCHAR* MakeStringFromPlainText (const TCHAR* szPlainText, CVolString* pstrResult, const BOOL_P blpEncloseEmptyStr);

//-----------------------------------------------  数值处理

// 将指定FLOAT以指定因子对齐到整数
inline_ INT_P AlignFloatToInt (const FLOAT f, const FLOAT fDiv)
{
    ASSERT (fDiv > 0.0f);

    if (f < 0.0f)  // 如果小于0,对齐值的起始值为-1.
        return (INT_P)(f / fDiv) - 1;
    else  // 如果大于等于0,对齐值的起始值为0.
        return (INT_P)(f / fDiv);
}

inline_ INT_P AlignIntToInt (const INT_P np, const INT_P npDiv)
{
    ASSERT (npDiv > 0);

    if (np < 0)  // 如果小于0,对齐值的起始值为-1.
        return np / npDiv - 1;
    else  // 如果大于等于0,对齐值的起始值为0.
        return np / npDiv;
}

// 将指定FLOAT以指定因子对齐到FLOAT
inline_ FLOAT AlignFloat (const FLOAT f, const FLOAT fDiv)
{
    ASSERT (fDiv > 0.0f);
    return (FLOAT)AlignFloatToInt (f, fDiv) * fDiv;
}

INT_P ClampInt (const INT_P npValue, const INT_P npMinimum, const INT_P npMaximum);
FLOAT ClampFloat (const FLOAT fValue, const FLOAT fMinimum, const FLOAT fMaximum);

FLOAT AmendRadian (FLOAT fRadian);  // 将任意角度转换到-180度到180度之间.
INT_P LargestOrEqualPower2 (INT_P x);  // 获得大于或等于x的2的power值

// 获得up值的最后一个bit
inline_ UINT_P GetLowestOneBit (const UINT_P up)
{
    return (up & (~up + 1));
}

// 根据调节量将fCurrent靠近fDest,返回调节后的值.
//   fCurrent: 当前值
//   fDest: 目的值
//   fAdjustValue: 调节量,必须大于0.
FLOAT FloatCloseTo (FLOAT fCurrent, const FLOAT fDest, const FLOAT fAdjustValue);

// 返回数值的符号位
inline_ INT_P GetSign (const INT n)  {  return (n < 0 ? -1 : n > 0 ? 1 : 0);  }
inline_ INT_P GetSign (const INT64 n64)  {  return (n64 < 0 ? -1 : n64 > 0 ? 1 : 0);  }
inline_ INT_P GetSign (const DOUBLE db)  {  return (db > NEAR_ZERO_DOUBLE ? 1 : db < -NEAR_ZERO_DOUBLE ? -1 : 0);  }

INT_P FloorDouble (const DOUBLE dbValue);
INT_P FixDouble (const DOUBLE dbValue);
DOUBLE RoundDouble (DOUBLE db, const INT_P npRound);

inline_ INT RoundDoubleToInt (DOUBLE dbValue)
{
    return (INT)(dbValue + 0.5);
}

//-----------------------------------------------  随机数处理

void SetRandSeed (INT_P npSeed);
DOUBLE randdouble ();  // 返回一个0.0f到1.0f(包括0.0f和1.0f)之间的随机浮点数
DOUBLE randdouble (const DOUBLE dbFrom, const DOUBLE dbTo);  // 返回一个在fFrom到fTo之间的随机浮点数(包括fFrom和fTo本身)
INT_P randint ();  // 返回一个0到 RAND_MAX(32767)之间的一个伪随机整数
INT_P randint (const INT_P upper);  // 返回一个范围在0和upper(包括0和upper本身)之间的随机整数
INT_P randint (INT_P lower, INT_P upper);  // 返回一个范围在lower和upper(包括lower和upper本身)之间的随机整数
DWORD randdword ();  // 返回一个0到0xFFFFFFFF之间的一个伪随机DWORD
INT randint2 (INT lower, INT upper);  // 返回一个范围在lower和upper(包括lower和upper本身)之间的随机整数,并不限定在32627之内.

// 投掷所指定面数的骰子,返回其是否正面(即0面)朝上.
inline_ BOOL_P RollDice (const INT_P npNumDiceFace)
{
    ASSERT (npNumDiceFace > 1);  // 骰子面数必须大于1(等于1没有意义)
    return ((randint () % npNumDiceFace) == 0);
}

template<typename N> N NumberAlignUp (N n, ULONG nAlign)
{
    return (N ((n + (nAlign - 1)) & ~(N (nAlign) - 1)));
}

template<typename N> N NumberlAlignDown (N n, ULONG nAlign)
{
    return (N (n & ~ (N (nAlign) - 1)));
}

//-----------------------------------------------  文本Hash操作

// 返回szText文本的Hash值. 如果szText不为空文本,则所返回的Hash值必定不为0.
//   pnpTextLength: 如果不为NULL,在其中返回文本的长度.
template<class T> UINT_P tGetTextHash (const T* szText, INT_P* pnpTextLength)
{
    ASSERT_R_STR (szText);
    ASSERT_RW_DATA_OR_NULL (pnpTextLength);

    if (szText == NULL || *szText == '\0')
    {
        if (pnpTextLength != NULL)
            *pnpTextLength = 0;
        return 0;
    }

    const T* ps = szText;

    // BKDR String Hash Function
    UINT_P upHash = 0;
    while (TRUE)
    {
        const UINT_P upChar = (UINT_P)*ps;
        if (upChar == '\0')
            break;

        upHash = upHash * 5 + upChar;  // 注意乘数必须是质数
        ps++;
    }

    if (pnpTextLength != NULL)
        *pnpTextLength = ps - szText;
    return (upHash | 1);  // 确保返回值不为0
}

// 返回指定长度的psText文本的Hash值. 如果psText不为空文本,则所返回的Hash值必定不为0.
// 注意: 本函数中的算法必须与tGetTextHash中的一致
template<class T> UINT_P tGetTextWithLenHash (const T* psText, const INT_P npTextLength)
{
    ASSERT_R_STR2 (psText, npTextLength);

    if (npTextLength == 0)
        return 0;
    ASSERT (psText != NULL);

    // 获得文本结束指针位置
    const T* psTextEnd = psText + npTextLength;

    // BKDR String Hash Function
    UINT_P upHash = 0;
    for (; psText < psTextEnd; psText++)
    {
        upHash = upHash * 5 + (UINT_P)*psText;  // 注意乘数必须是质数
    }

    return (upHash | 1);  // 确保返回值不为0
}

// 返回szText文本的字母大小写无关Hash值. 如果szText不为空文本,则所返回的Hash值必定不为0.
template<class T> UINT_P tGetTextIHash (const T* szText, INT_P* pnpTextLength)
{
    ASSERT_R_STR (szText);
    ASSERT_RW_DATA_OR_NULL (pnpTextLength);

    if (szText == NULL || *szText == '\0')
    {
        if (pnpTextLength != NULL)
            *pnpTextLength = 0;
        return 0;
    }

    const T* ps = szText;

    UINT_P upHash = 0;
    while (TRUE)
    {
        const UINT_P upChar = (UINT_P)*ps;
        if (upChar == '\0')
            break;

        upHash *= 5;  // 必须是质数
        if (upChar >= 'a' && upChar <= 'z')  // 为小写字母?
            upHash += (upChar - 'a' + 'A');  // 转换为大写字母加入
        else
            upHash += upChar;

        ps++;
    }

    if (pnpTextLength != NULL)
        *pnpTextLength = ps - szText;
    return (upHash | 1);  // 确保返回值不为0
}

// 返回指定长度的psText文本的字母大小写无关Hash值. 如果psText不为空文本,则所返回的Hash值必定不为0.
// 注意: 本函数中的算法必须与tGetTextIHash中的一致
template<class T> UINT_P tGetTextWithLenIHash (const T* psText, const INT_P npTextLength)
{
    ASSERT_R_STR2 (psText, npTextLength);

    if (npTextLength == 0)
        return 0;
    ASSERT (psText != NULL);

    // 获得文本结束指针位置
    const T* psTextEnd = psText + npTextLength;

    // BKDR String Hash Function
    UINT_P upHash = 0;
    for (; psText < psTextEnd; psText++)
    {
        const UINT_P upChar = (UINT_P)*psText;

        upHash *= 5;  // 必须是质数
        if (upChar >= 'a' && upChar <= 'z')  // 为小写字母?
            upHash += (upChar - 'a' + 'A');  // 转换为大写字母加入
        else
            upHash += upChar;
    }

    return (upHash | 1);  // 确保返回值不为0
}

// 返回指定文本的Hash值
//   pnpTextLength: 如果不为NULL,在其中返回文本的长度.
inline_ DWORD GetTextHash (const WCHAR* pws, INT_P* pnpTextLength = NULL)
{
    return (DWORD)(tGetTextHash (pws, pnpTextLength) & 0x7FFFFFFF);
}
inline_ DWORD GetTextHash (const U8CHAR* ps, INT_P* pnpTextLength = NULL)
{
    return (DWORD)(tGetTextHash (ps, pnpTextLength) & 0x7FFFFFFF);
}
inline_ DWORD GetTextWithLenHash (const WCHAR* pws, const INT_P npTextLength)
{
    return (DWORD)(tGetTextWithLenHash (pws, npTextLength) & 0x7FFFFFFF);
}
inline_ DWORD GetTextWithLenHash (const U8CHAR* ps, const INT_P npTextLength)
{
    return (DWORD)(tGetTextWithLenHash (ps, npTextLength) & 0x7FFFFFFF);
}

// 返回指定文本的字母大小写无关Hash值
//   pnpTextLength: 如果不为NULL,在其中返回文本的长度.
inline_ DWORD GetTextIHash (const WCHAR* pws, INT_P* pnpTextLength = NULL)
{
    return (DWORD)(tGetTextIHash (pws, pnpTextLength) & 0x7FFFFFFF);
}
inline_ DWORD GetTextIHash (const U8CHAR* ps, INT_P* pnpTextLength = NULL)
{
    return (DWORD)(tGetTextIHash (ps, pnpTextLength) & 0x7FFFFFFF);
}
inline_ DWORD GetTextWithLenIHash (const WCHAR* pws, const INT_P npTextLength)
{
    return (DWORD)(tGetTextWithLenIHash (pws, npTextLength) & 0x7FFFFFFF);
}
inline_ DWORD GetTextWithLenIHash (const U8CHAR* ps, const INT_P npTextLength)
{
    return (DWORD)(tGetTextWithLenIHash (ps, npTextLength) & 0x7FFFFFFF);
}

// 返回指定数据块的Hash
DWORD GetBinHash (const BYTE* pData, const INT_P npDataSize);

//-----------------------------------------------  文件和路径

// 返回当前进程所处的目录,成功返回真,失败返回假,所返回文本以OS_PATH_CHAR结束.
BOOL_P GetInstancePath (CVolString& strPath);

// 返回szOSPath是否为绝对路径
BOOL_P IsAbsPath (const TCHAR* szOSPath);

// 将路径szCheckAbsPath相对于szRootAbsPath路径的相对路径(无法转换将返回原路径名),并填写到strRelPath中返回.
// 注意: szCheckAbsPath和szRootAbsPath必须都是绝对路径
// 所返回路径目录必定以路径分隔符结束
const TCHAR* AbsPath2Rel (const TCHAR* szRootAbsPath, const TCHAR* szCheckAbsPath, CVolString& strRelPath);

// 将szCheckAbsPathFileName绝对路径文件名转换到基于szRootAbsPath目录的相对路径文件名,并填写到strRelPathFileName中返回.
// 无法转换将返回原文件名
const TCHAR* AbsPathFileName2Rel (const TCHAR* szRootAbsPath, const TCHAR* szCheckAbsPathFileName, CVolString& strRelPathFileName);

// 如所指定文件名中存在路径部分,将其填入strPath后返回(必定以OS_PATH_CHAR结束),否则返回空文本.
const TCHAR* GetOSFilePathPart (const TCHAR* szFileName, CVolString& strPath);

// 如果szFullFileName为全路径文件名,则返回其中的路径部分.
// 注意所返回路径尾部不会包括额外的OS_PATH_CHAR字符.
const TCHAR* GetAbsOSPathOfFileName (const TCHAR* szFullFileName, CVolString& strPath);

// 返回szFileName的无路径部分
const TCHAR* GetOSFileNameWithoutPath (const TCHAR* szFileName);

// 返回szFileName的无路径及无后缀部分
const TCHAR* GetOSFilePureName (const TCHAR* szFileName, CVolString& strBuf);

// 改变szFileName的文件后缀名后返回
// 注意szNewExt不包括前缀句点
CVolString ChangeFileNameExt (const TCHAR* szFileName, const TCHAR* szNewExt);

// 寻找文件名的后缀句点字符位置,未找到则返回NULL.
inline_ const TCHAR* FindFileNameExtDotChar (const TCHAR* szFileName)
{
    ASSERT_R_STR (szFileName);
    return _tcsrchr (GetOSFileNameWithoutPath (szFileName), '.');
}

// 返回指定文件名的后缀名称(注意不包括'.'字符),如果不存在则返回空文本.
const TCHAR* GetFileExtName (const TCHAR* szFileName);

// 删除所指定文件
BOOL_P MRemoveFile (const TCHAR* szFileName);

// 创建指定目录(包括所有中间目录),成功返回真,失败返回假.
BOOL_P CreateDirectoryTree (const TCHAR* szOSDirectoryName);

// 将当前目录填入到psBuf中,成功返回真,失败返回假.
//   npBufLength: 提供psBuf缓冲区以TCHAR为单位的尺寸
BOOL_P MGetCurrentDirectory (TCHAR* psBuf, const INT_P npBufLength);

// 设置当前目录为szNewDir,成功返回真,失败返回假.
BOOL_P MSetCurrentDirectory (const TCHAR* szNewDir);

// 将操作系统目录szPath1和szPath2连接起来,返回新路径文本.
//   memBuf参数提供一个缓冲区对象,用作在需要时保存返回路径.
// 本方法可以处理类似 "c:\test" 与 "..\data" 之间的连接,连接后的结果为 "c:\data".
// 在以下几种情况下,本方法将直接返回szPath2:
//   1. szPath2为绝对路径;
//   2. szPath2使用".."回溯超过了szPath1的范围,譬如上面的例子szPath2如果为"..\..\data",那么本方法将直接返回szPath2.
const TCHAR* LinkOSPath (const TCHAR* szPath1, const TCHAR* szPath2, CVolMem& memBuf, const TCHAR cPathChar = OS_PATH_CHAR);

// 返回指定目录/文件是否存在
BOOL_P IsOSFileExist (const TCHAR* szFileName);

// 如果szPath以可以被删除的路径字符结束,则将该路径字符删除后返回.
const TCHAR* RemoveEndPathChar (const TCHAR* szPath, CVolString& strBuf);

#ifdef _PF_WINDOWS

// 返回所指定文件名是否为".'"或".."名称
BOOL_P IsDotSubDirName (const TCHAR* szFileName);

// 删除指定目录,在Windows下自动删除其中所有子目录(blpOnlyRemoveFile为假时)和文件.
typedef enum
{
    DTRM_REMOVE_ALL = 0,     // 删除所指定目录及其中的所有内容
    DTRM_ONLY_REMOVE_FILES,  // 仅所指定目录中的所有文件
    DTRM_CLEAN_CONTENT       // 删除所指定目录中的所有内容,但是不删除所指定目录本身.
}
DIR_TREE_REMOVE_MODE;
// blpOnlyFailedWhileRemoveFile: 是否仅当删除文件失败时才会出错返回
BOOL_P RemoveDirectoryTree (const TCHAR* szOSDirectoryName, const DIR_TREE_REMOVE_MODE enRemoveMode, const BOOL_P blpOnlyFailedWhileRemoveFile);

// 返回指定实例句柄进程所处的目录,成功返回真,失败返回假,所返回文本以OS_PATH_CHAR结束.
BOOL_P GetInstancePath (const HINSTANCE hInstance, CVolString& strPath);

// 返回所指定的两个文件是否均存在且文件尺寸和最后修改时间都一致
BOOL_P IsFileSizeAndTimeSame (const TCHAR* szFileName1, const TCHAR* szFileName2);

// 拷贝文件,返回是否成功.
// 本函数能够处理源和目的文件名重名的情况
//   szSourceFileName: 欲拷贝的源文件名
//   szDestFileName: 欲拷贝到的目的文件名
//   enOverrideMode: 文件覆盖模式
typedef enum
{
    FCOM_OVERRIDE = 0,  // 如果所欲拷贝到的文件已经存在,则将其覆盖.
    FCOM_IGNORE,        // 如果所欲拷贝到的文件已经存在,则跳过不拷贝.
    FCOM_FAST,          // 如果所欲复制到的文件已经存在且其尺寸和最后修改时间与源文件一致,则跳过不复制,否则将其覆盖.
    FCOM_FAIL           // 如果所欲拷贝到的文件已经存在,则拷贝失败.
}
FILE_COPY_OVERRIDE_MODE;
BOOL_P MCopyFile (const TCHAR* szSourceFileName, const TCHAR* szDestFileName, const FILE_COPY_OVERRIDE_MODE enOverrideMode);

// 将文件拷贝到所指定目录,成功返回真,失败返回假.
// 如果目的文件所处目录不存在则自动创建
//   szSourceFileName: 欲拷贝的源文件名
//   szDestFileName: 欲拷贝到的目的文件名
//   enOverrideMode: 文件覆盖模式
BOOL_P MCopyFileAutoCreateDir (const TCHAR* szSourceFileName, const TCHAR* szDestFileName, const FILE_COPY_OVERRIDE_MODE enOverrideMode);

// 将szSrcOSDir目录中的所有与szMatchFiles匹配的文件复制到szDestOSDir目录中去. 全部复制成功返回真,存在文件/目录复制失败则返回假.
//   szSrcOSDir: 源目录,必须不为空文本.
//   szDestOSDir: 目的目录,必须不为空文本.
//   szMatchFiles: 所欲匹配的文件名,如果为空文本,则默认为"*.*".
//   blpFailIfExists: 如果目标文件存在是否跳过并报告失败
//   blpRecursiveSubDir: 是否递归复制子目录中的文件
//   psaryCopyFailFileNames: 如果不为NULL则将所有复制失败的源文件和目的文件名加入进去(每两个成员为一个记录).
// 成功返回真,失败返回假.
BOOL_P MCopyFiles (const TCHAR* szSrcOSDir, const TCHAR* szDestOSDir, const TCHAR* szMatchFiles,
        const FILE_COPY_OVERRIDE_MODE enFileCopyOverrideMode, const BOOL_P blpRecursiveSubDir, CMStringArray* psaryCopyFailFileNames);

// 注册文件关联
// szExeFileName: 要关联的应用程序文件名(例如: "C:\MyApp\MyApp.exe"),为空文本表示使用当前程序.
// szExtName: 要注册的扩展名(例如: ".txt"),需要以句点开始,不能为空文本.
// szExtKeyName: szExtName扩展名在注册表中的键值(例如: "txtfile"),不能为空文本.
// szModuleFileName: 被注册文件类型图标所处的文件名,为空文本表示使用当前程序.
// npIconIndex: 图标在szModuleFileName文件中的索引位置,为小于-1的负值表示为ID. 不能等于-1.
// szDescribe: 文件类型描述
void RegisterFileRelation (const TCHAR* szExeFileName, const TCHAR* szExtName, const TCHAR* szExtKeyName,
        const TCHAR* szModuleFileName, const INT_P npIconIndex, const TCHAR* szDescribe);

// 返回所指定名称文件的信息,成功返回真并将相关信息填入pinfFile中,失败返回假.
BOOL_P GetFileInfo (const TCHAR* szFileName, WIN32_FIND_DATA* pinfFile);

// 寻找指定目录内的所有匹配文件,返回所找到文件的数目.
//   szFindDir: 所欲查找的目录名
//   szMatchFileName: 匹配模板文件名
//   blpFindSubDirName: 为真则去查找子目录名,否则去查找非子目录文件名.
//   saryFoundFileNames: 用作存放查找结果
//   blpAddDir: 存放查找结果文件名到saryFoundFileNames中时是否加上路径名
INT_P FindAllMatchFiles (const TCHAR* szFindDir, const TCHAR* szMatchFileName, const BOOL_P blpFindSubDirName,
        CMStringArray& saryFoundFileNames, const BOOL_P blpAddDir);

// 激活其它应用程序的窗口
void ActiveOtherAppWindow (HWND hWnd);

// 将szClipText文本置入剪贴版内,成功返回真,失败返回假.
BOOL_P SetClipboardText (const TCHAR* szClipText);

// 返回当前剪贴板中的文本,如果不存在则返回空文本.
const TCHAR* GetCurrentClipboardText (CVolMem& memBuf);

// 启动执行指定的命令行,返回是否成功.
//   blpWaitEnd: 是否一直等待所运行命令行结束
//   npShowWindow: 被启动程序的窗口显示方式,为ShowWindow的所有"SW_xxx"宏值,提供-1表示不指定.
BOOL_P RunCommandLine (const TCHAR* szCommandLine, const BOOL_P blpWaitEnd, const INT_P npShowWindow = -1, LPDWORD pdwExitCode = NULL, CVolString* pstrStdOut = NULL, CVolString* pstrStdError = NULL, const BOOL_P blpStdOutUTF8 = FALSE);

// 打开指定URL,返回是否成功.
//   npShowWindow: 被启动程序的窗口显示方式,为ShowWindow的所有"SW_xxx"宏值,提供-1表示使用默认方式.
#define _T_BROWSE_ITEM_HREF_LEADER  _T ("browse://")  // 用作在文件管理器中定位所指定文件使用
BOOL_P OpenURL (const TCHAR* szURL, const INT_P npShowWindow);

// 调用资源管理器打开szFileName文件所处的文件夹并将其选中
void ShellOpenFileInsideFolder (const TCHAR* szFileName);

DOUBLE GetSystemUIScale ();

// 返回指定窗口句柄所处显示器的当前DPI(缩放比例).
// hWnd: 提供所欲检查窗口句柄,为NULL表示使用桌面窗口(主显示器).
DOUBLE GetMoniterDPI (HWND hWnd);

// 设置对DPI变化的关注模式
void MSetProcessDpiAwareness (INT nMode);

// 返回当前进程是否存在顶层窗口
BOOL_P IsCurrentProcessHasTopWindow (const HWND hExcludeWnd);

// 解锁并释放所指定的全局内存句柄
void GlobalUnlockAndFree (const HGLOBAL hGlobal);

// 返回系统中的CPU数目
INT_P GetNumProcessorsInsideSystem ();

// 返回多线程程序推荐使用的工作线程数目
INT_P GetRecommendWorkingThreadCount (const INT_P npMaxThreadCount);

// 是否允许拖放文件
void MyDragAcceptFiles (HWND hWnd, BOOL_P blpEnable);

//-----------------------------------------------  运行控制台程序

typedef struct
{
    DWORD m_dwRunningTime;  // 从开始执行控制台程序时到现在所已经经过的时间(单位毫秒)
    BOOL_P m_blpProcessExited;  // 如果程序已经执行完毕,则会最后调用本超时检查函数一次(注意此时超时检查周期可能并未到达),此时本成员值为真.

    const TCHAR* m_szCommandLine;  // 被执行的命令行文本,必定不为空文本.
    CVolMem* m_pmemStdOutWideText;  // 必定不为NULL,提供当前已经获取的标准输出文本(宽字符集),以'\0'结束.超时处理函数可以修改或删除其中的内容.
    CVolMem* m_pmemStdErrorWideText;  // 必定不为NULL,提供当前已经获取的标准错误输出文本(宽字符集),以'\0'结束.超时处理函数可以修改或删除其中的内容.
    UINT_P m_upUserData1, m_upUserData2;  // 调用RunConsoleApp时CONSOLE_APP_TIME_OUT_CHECK_PARAM参数中所提供的值
}
TIME_OUT_CALL_BACK_PARAM;
// 用作判断执行是否超时
//   pCallbackParam: 回调参数,必定不为NULL.
typedef enum
{
    TOCR_CONTINUE = 0,  // 继续执行
    TOCR_EXIT,          // 返回需要退出所执行程序(不标记超时状态)
    TOCR_TIME_OUT       // 返回被执行程序已经超时
}
TIME_OUT_CHECK_RESULT;
typedef TIME_OUT_CHECK_RESULT (*FN_IS_TIME_OUT) (const TIME_OUT_CALL_BACK_PARAM* pCallbackParam);

typedef struct
{
    FN_IS_TIME_OUT m_fnIsTimeout;  // 超时检查函数,不能为NULL.
    UINT_P m_upNotifyInterval;  // 提供调用m_fnIsTimeout函数的时间间隔(单位毫秒)
    UINT_P m_upUserData1, m_upUserData2;  // 原值传递给m_fnIsTimeout函数
}
CONSOLE_APP_TIME_OUT_CHECK_PARAM;

typedef enum
{
    CARR_SUCCEEDED =  0,  // 执行成功
    CARR_FAIL      = -1,  // 执行失败
    CARR_TIMEOUT   = -2,  // 超出最大等待时间
}
CONSOLE_APP_RUN_RESULT;

// 控制台程序所输出字符编码的格式
typedef enum
{
    CAOCS_MBS = 0,  // 本地多字节编码
    CAOCS_UTF8,     // UTF8编码
}
CONSOLE_APP_OUT_CHAR_SET;

// 执行指定的控制台程序且一直等待其退出,获取其标准输出和标准错误输出文本. 返回是否成功.
//   szEnvironmentData: 如果不为NULL,则提供启动环境数据.
//   szCommandLine: 欲执行的控制台命令行
//   szWorkingPath: 工作目录,如果为空文本则自动从szCommandLine中去获取,为NULL则使用调用进程的当前目录.
//   enOutCharSet: 提供控制台程序所输出字符编码的格式
//   pstrStdOut: 如果不为NULL,则在其中返回该程序的标准输出文本.
//   pstrStdError: 如果不为NULL,则在其中返回该程序的标准错误输出文本. 可以等于pstrStdOut,此时标准错误输出文本将附加在后面.
//   blpRemoveAllEmptyLines: 是否删除在*pstrStdOut和*pstrStdError中所返回文本中的所有空白行
//   pdwAppExitCode: 如果不为NULL,则在其中返回所运行程序的退出值.
//   pTimeoutCheckParam: 如果不为NULL,则提供超时检查参数.
CONSOLE_APP_RUN_RESULT RunConsoleAppWithEnv (const TCHAR* szEnvironmentData, const TCHAR* szCommandLine, const TCHAR* szWorkingPath,
        const CONSOLE_APP_OUT_CHAR_SET enOutCharSet, CVolString* pstrStdOut, CVolString* pstrStdError,
        const BOOL_P blpRemoveAllEmptyLines, DWORD* pdwAppExitCode, const CONSOLE_APP_TIME_OUT_CHECK_PARAM* pTimeoutCheckParam);
    
inline_ CONSOLE_APP_RUN_RESULT RunConsoleApp (const TCHAR* szCommandLine, const TCHAR* szWorkingPath,
        const CONSOLE_APP_OUT_CHAR_SET enOutCharSet, CVolString* pstrStdOut, CVolString* pstrStdError,
        const BOOL_P blpRemoveAllEmptyLines, DWORD* pdwAppExitCode, const CONSOLE_APP_TIME_OUT_CHECK_PARAM* pTimeoutCheckParam)
{
    return RunConsoleAppWithEnv (NULL, szCommandLine, szWorkingPath, enOutCharSet, pstrStdOut, pstrStdError,
            blpRemoveAllEmptyLines, pdwAppExitCode, pTimeoutCheckParam);
}

// 同上函数,只是将结果自动分行.
CONSOLE_APP_RUN_RESULT RunConsoleAppAndWrapLines (const TCHAR* szCommandLine, const TCHAR* szWorkingPath,
        const CONSOLE_APP_OUT_CHAR_SET enOutCharSet, CMStringArray* psaryStdOutLines, CMStringArray* psaryStdErrorLines,
        const BOOL_P blpRemoveAllEmptyLines, DWORD* pdwAppExitCode, const CONSOLE_APP_TIME_OUT_CHECK_PARAM* pTimeoutCheckParam);

// dwMaxWaitMillseconds: 操作结束最大等待毫秒数,为0表示无限等待.
CONSOLE_APP_RUN_RESULT RunConsoleAppWithTimeoutCheck (const TCHAR* szCommandLine, const TCHAR* szWorkingPath,
        const CONSOLE_APP_OUT_CHAR_SET enOutCharSet, CVolString* pstrStdOut, CVolString* pstrStdError,
        const BOOL_P blpRemoveAllEmptyLines, DWORD* pdwAppExitCode, const DWORD dwMaxWaitMillseconds);

#endif

//-----------------------------------------------  动态库处理

typedef UINT_P H_LIB;  // 动态库句柄,0表示为无效句柄.

// 动态连接库的默认后缀名称
#if defined (_PF_WINDOWS)
    #define _LIB_EXT_NAME  _T (".dll");
#elif defined (_PF_LINUX)
    #define _LIB_EXT_NAME  _T (".so");
#endif

// 载入指定文件名的动态库,成功返回其句柄,失败返回0.
H_LIB MLoadLibrary (const TCHAR* szLibraryName);

// 释放先前所载入的动态库,成功返回真,失败返回假.
BOOL_P MFreeLibrary (const H_LIB hLibraryModule);

// 返回指定动态库中所输出的指定名称程序地址,未找到返回NULL.
VOID_FUNC MGetProcAddress (const H_LIB hLibraryModule, const U8CHAR* szProcName);

//-----------------------------------------------  数组操作

#define SORT_INT_ARRAY(nary,ascend)  MSortIntArray ((nary), NUM_ELEMENTS_OF (nary), (ascend))
#define SORT_DOUBLE_ARRAY(dbary,ascend)  MSortDoubleArray ((dbary), NUM_ELEMENTS_OF (dbary), (ascend))

void MSortIntArray (INT* pnArray, const INT_P npNumElements, const BOOL_P blpAscend);
void MSortDoubleArray (DOUBLE* pdbArray, const INT_P npNumElements, const BOOL_P blpAscend);

//-----------------------------------------------  杂类

#ifdef _PF_WINDOWS

// 以二进制数据方式读写指定注册表项. 写入时如果不存在则自动创建.
BOOL_P MGetProfileBinary (const TCHAR* szSection, const TCHAR* szEntry, CVolMem* pMem);
BOOL_P MSetProfileBinary (const TCHAR* szSection, const TCHAR* szEntry, const BYTE* pData, const DWORD dwBytes);
BOOL_P MGetProfileBinary (const TCHAR* szSection, const TCHAR* szEntry, CVolMem* pMem, const INT_P npRequiredSize);

// 获取hWnd窗口所处显示器屏幕的显示区域
//   hWnd: 欲检查的窗口句柄,如果为NULL,则获取主显示器屏幕的显示区域.
//   prtMonitor: 用作返回显示区域矩形,不能为NULL. 注意: 在多显示器环境中坐标值可能为负值,这是正常的.
void GetMonitorRect (const HWND hWnd, RECT* prtMonitor);

// 将hWnd窗口在其父窗口所处监视器屏幕中居中
//   npWindowWidth, npWindowHeight: hWnd窗口欲设置的宽度和高度
void CenterWindowInsideMonitor (const HWND hWnd, const INT_P npWindowWidth, const INT_P npWindowHeight);

// 将clr颜色的各分量分别乘于dbMulValue,返回相乘后的结果.
COLORREF MulRGB (const COLORREF clr, const DOUBLE dbMulValue);

// 获取当前模块自身的句柄(在DLL中调用将返回自身实例句柄,而不会返回所处进程的实例句柄),失败返回NULL.
HMODULE GetSelfModuleHandle ();

// 返回使用所指定字体绘制所指定文本所需要的尺寸
SIZE GetTextDrawSize (HFONT hFont, const TCHAR* szText);

// 载入所指定名称的系统库
HINSTANCE MLoadSystemLibrary (const TCHAR* szLibPureFileName);

INT MGetStretchMode ();
INT GetCommandLineArray (CMStringArray& saryArgs);

//-----------------------------------------------------------------------------------

// 将屏幕字体实际尺寸(单位像素)转换为逻辑尺寸(单位磅/点)
DOUBLE DoubleFontDpSize2Pt (const DOUBLE dbFontDpSize);
inline_ INT_P FontDpSize2Pt (const INT_P npFontDpSize)
{
    return (INT_P)(DoubleFontDpSize2Pt ((DOUBLE)npFontDpSize) + 0.5);
}

// 将屏幕字体逻辑尺寸(单位磅/点)转换为实际尺寸(单位像素)
DOUBLE DoubleFontPtSize2Dp (const DOUBLE dbFontPtSize);
inline_ INT_P FontPtSize2Dp (const INT_P npFontPtSize)
{
    return (INT_P)(DoubleFontPtSize2Dp ((DOUBLE)npFontPtSize) + 0.5);
}

// 返回默认字体信息
void GetDefaultFontInfo (LOGFONT* pinfFont);

// 将szFontDescText字体描述文本所对应的字体信息填入*pinfFont中
//   szFontDescText格式为: "字体名, 字体尺寸, 是否为粗体, 是否为斜体, 是否有下划线, 是否有删除线, 旋转角度",
//                         其中"是否"字段,用1代表真,0代表假.字体尺寸单位为磅, 旋转角度单位为1/10度.
void GetFontDescTextInfo (const TCHAR* szFontDescText, LOGFONT* pinfFont);

// 根据infFont信息构建对应的字体描述文本,将其填入strFontDesc中后返回.
const TCHAR* GetFontDescText (const LOGFONT& infFont, CVolString& strFontDesc);

// 返回对应clrText的真实文本颜色
inline_ COLORREF GetRealTextColor (COLORREF clrText)
{
    return (clrText == CLR_DEFAULT ? ::GetSysColor (COLOR_WINDOWTEXT) : clrText);
}

// 返回对应clrBack的真实背景颜色
inline_ COLORREF GetRealBackColor (COLORREF clrBack)
{
    return (clrBack == CLR_DEFAULT ? ::GetSysColor (COLOR_BTNFACE) : clrBack);
}

// 关闭Windows操作系统
//   npMode: 1:关机; 2:重启; 3:注销; 4:休眠; 5:冬眠.
//   blpForceExit: 是否强制关闭
BOOL_P ExitWindowSystem (const INT_P npMode, const BOOL_P blpForceExit);

// 获取hBitmap位图所对应的ImageList单个项目尺寸
BOOL_P GetImageListItemSize (const HBITMAP hBitmap, SIZE* psizeItem);

#endif

// 休眠指定毫秒数
inline_ void MSleep (const INT_P npMillisecond)
{
    if (npMillisecond > 0)
    {
    #if defined (_PF_WINDOWS)
        ::Sleep ((DWORD)npMillisecond);
    #elif defined (_PF_LINUX)
        timespec ts;
        ts.tv_sec = npMillisecond / 1000;
        ts.tv_nsec = ((long)npMillisecond % 1000) * 1000 * 1000;  // Convert millseconds into nanoseconds.
        ::nanosleep (&ts, NULL);
        // usleep (npMillisecond * 1000);
    #endif
    }
}

// 当在Windows调试版本中时,输出最后一个Windows错误信息
#if defined (_DEBUG) && defined (_PF_WINDOWS)
    void TrackWinLastError ();
    #define TRACE_WIN_LAST_ERROR  TrackWinLastError ();
#else
    #define TRACE_WIN_LAST_ERROR
#endif

// 反转pbData缓冲区内npDataSize字节的内容
void ReverseBytes (BYTE* pbData, const INT_P npDataSize);

// 反转wValue值中的字节顺序,返回反转后的值.
WORD ReverseWordBytes (const WORD wValue);

// 反转dwValue值中的字节顺序,返回反转后的值.
DWORD ReverseDWordBytes (const DWORD dwValue);

// 使用dwXorValue对pData,npDataSize数据进行异或
void XorData (void* pData, const INT_P npDataSize, const DWORD dwXorValue);

// 返回pData,npDataSize数据异或后的值
DWORD GetDataXorValue (const void* pData, const INT_P npDataSize);

// 将所指定数据写入szFileName文件中,返回是否写入成功.
//   szFileName: 欲写出到的文件名
//   pData, npDataSize: 欲写出的文件数据
BOOL_P WriteDataIntoFile (const TCHAR* szFileName, const void* pData, const INT_P npDataSize);

// 输出所指定火山类型的调试数据行
//   blpStringFormatText: 是否使用字符串格式来输出文本数据
//   nMaxDumpSize: 提供用户所指定的最大允许展示数据尺寸,小于0表示全部展示,等于0表示展示默认尺寸数据.
//   npFirstExtendParamTypeIndex: 第一个扩展参数的类型在szParamTypes中的索引位置
void DebugTrace (const BOOL_P blpStringFormatText, const INT nMaxDumpSize, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, ...);
void DebugTraceWithSourcePos (const TCHAR* szSourceFileName, const TCHAR* szLineNumber, const BOOL_P blpStringFormatText,
        const INT nMaxDumpSize, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, ...);
void DebugMessageBox (const BOOL_P blpStringFormatText, const INT nMaxDumpSize, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, ...);
CVolString& DebugGetDumpString (const BOOL_P blpStringFormatText, const INT nMaxDumpSize, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, CVolString* pstrDebug, ...);
const TCHAR* AddDebugDumpString (const BOOL_P blpStringFormatText, const INT nMaxDumpSize,
        const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, CVolString& strDebug, va_list argList);

// 收集所有提供过来的火山参数数据. 支持所有火山基本数据类型和字节集类数据.
// 注意: 对应火山嵌入式方法必须定义了值为真的 "req_obj_param_pointer" 和 "req_str_param_text_pointer" 属性.
CVolMem& CollectVariantVolDatas (CVolMem& memData, const TCHAR* szParamTypes, ...);
CVolMem& CollectVariantListVolDatas (CVolMem& memData, const TCHAR* szParamTypes, va_list argList);

// 返回所指定可执行文件适用到的机器类型(IMAGE_FILE_MACHINE_xxx系列宏值)
INT_P GetImageFileMachineType (const TCHAR* szFileName);

// 返回所指定可执行文件适用到的机器CPU位数
typedef enum
{
    IFMBC_UNKNOWN = -1,
    IFMBC_WIN32,
    IFMBC_X64
}
IMAGE_FILE_MACHINE_BITS_COUNT;
IMAGE_FILE_MACHINE_BITS_COUNT GetImageFileMachineBits (const TCHAR* szFileName);

S_BYTE ChooseOneValue_S_BYTE (INT_P npValueIndex, const INT_P npNumValues, ...);
SHORT ChooseOneValue_SHORT (INT_P npValueIndex, const INT_P npNumValues, ...);
TCHAR ChooseOneValue_TCHAR (INT_P npValueIndex, const INT_P npNumValues, ...);
INT ChooseOneValue_INT (INT_P npValueIndex, const INT_P npNumValues, ...);
INT64 ChooseOneValue_INT64 (INT_P npValueIndex, const INT_P npNumValues, ...);
FLOAT ChooseOneValue_FLOAT (INT_P npValueIndex, const INT_P npNumValues, ...);
DOUBLE ChooseOneValue_DOUBLE (INT_P npValueIndex, const INT_P npNumValues, ...);
BOOL ChooseOneValue_BOOL (INT_P npValueIndex, const INT_P npNumValues, ...);
CVolString& ChooseOneValue_CVolString (INT_P npValueIndex, const INT_P npNumValues, ...);

COLORREF OffsetColor (const COLORREF clr, INT_P npOffset);

void ProcessCurrentChildTabChanged (HWND hTabWnd);
void SetFocusToFisrtFocusableChildControl (HWND hWnd);
INT GetVolControlGroupNumber (HWND hControlWnd);
BOOL SetVolControlGroupNumber (HWND hControlWnd, INT nNewGroupNumber);
void NotifyParentCurrentChildTabChanged (HWND hTabWnd, const BOOL_P blpPostMessage);
BOOL IsVolControlVisible (HWND hControlWnd);
void ShowVolControl (HWND hControlWnd, BOOL_P blpVisible);

#endif
