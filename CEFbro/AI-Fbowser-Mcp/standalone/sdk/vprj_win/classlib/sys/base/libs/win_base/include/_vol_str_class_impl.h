
// Copyright (C) Recursion Company. All rights reserved.

#include "_vol_str_macro.h"

// 文本类的默认对齐字符数
#define _DEFAULT_TEXT_ALIGN_CHARS  127

#ifdef _MY_WSTRING_IMPL
class CU8String;
#else
class CWString;
#endif

// 火山文本对象类
class _MY_STRING : public CVolObject
{
    DECLARE_GLOBAL_VOL_CLASS_NOT_OVR_COMP (_MY_STRING)

public:
    inline_ _MY_STRING ()
    {
        m_szConstText = NULL;
        SetNumAlignChars (_DEFAULT_TEXT_ALIGN_CHARS);
    }

#ifdef _MY_WSTRING_IMPL
    _MY_STRING (const CU8String& str);
#else
    _MY_STRING (const CWString& str);
#endif

    inline_ _MY_STRING (const _MYS_TCHAR* ps) : _MY_STRING ()       {  AddText (ps);  }
    inline_ _MY_STRING (const _MYS_OTHER_CHAR* ps) : _MY_STRING ()  {  AddText (ps);  }
#if (defined (_MY_WSTRING_IMPL) && defined (_UNICODE))  // 为实现宽文本对象且为编译Unicode版本?
    inline_ _MY_STRING (const S_BYTE sb) : _MY_STRING ()            {  AddIntText ((INT)sb);  }
#endif
    inline_ _MY_STRING (const SHORT sht) : _MY_STRING ()            {  AddIntText ((INT)sht);  }
    inline_ _MY_STRING (const _MYS_TCHAR ch) : _MY_STRING ()        {  AddChar (ch);  }
    inline_ _MY_STRING (const INT n) : _MY_STRING ()                {  AddIntText (n);  }
    inline_ _MY_STRING (const INT64 n64) : _MY_STRING ()            {  AddInt64Text (n64);  }
    inline_ _MY_STRING (const FLOAT flt) : _MY_STRING ()            {  AddFloatText (flt);  }
    inline_ _MY_STRING (const DOUBLE db) : _MY_STRING ()            {  AddDoubleText (db);  }

    inline_ _MY_STRING (const UCHAR bt) : _MY_STRING ()             {  AddIntText ((INT)(DWORD)bt);  }
    inline_ _MY_STRING (const USHORT w) : _MY_STRING ()             {  AddIntText ((INT)(DWORD)w);  }
    inline_ _MY_STRING (const UINT dw) : _MY_STRING ()              {  AddIntText ((INT)dw);  }
    inline_ _MY_STRING (const DWORD dw) : _MY_STRING ()             {  AddIntText ((INT)dw);  }
    inline_ _MY_STRING (const UINT64 u64) : _MY_STRING ()           {  AddUInt64Text (u64);  }

    inline_ _MY_STRING (const _MYS_TCHAR* ps, const INT_P npLen) : _MY_STRING ()
    {
        CheckSetText (ps, npLen);
    }

    inline_ _MY_STRING (const _MYS_OTHER_CHAR* ps, const INT_P npLen) : _MY_STRING ()
    {
        SetText (ps, npLen);
    }

    inline_ static _MY_STRING sGetRepeatCharText (const _MYS_TCHAR ch, const INT_P npNumChars)
    {
        _MY_STRING str;
        str.AddChar (ch, npNumChars);
        return str;
    }

    static _MY_STRING sGetRepeatText (const _MYS_TCHAR* szText, const INT_P npNumRepeat);

public:
    inline_ INT_P GetNumAlignChars () const
    {
        return m_mem.GetMemAlignSize () / sizeof (_MYS_TCHAR);
    }

    inline_ void SetNumAlignChars (const INT_P npNumAlignChars)
    {
        ASSERT (npNumAlignChars >= 0);
        m_mem.SetMemAlignSize (sizeof (_MYS_TCHAR) * npNumAlignChars);
    }

    inline_ operator const _MYS_TCHAR* () const
    {
        return GetText ();
    }

    // 返回文本指针,如果本对象为空对象,则返回NULL,否则必定不为NULL.
    inline_ const _MYS_TCHAR* _NAME_COMPILER_AGREED (GetTextMaybeNull) () const
    {
        return (IsNullObject () ? NULL : GetText ());
    }

    // 返回文本指针,必定不为NULL.
    const _MYS_TCHAR* _NAME_COMPILER_AGREED (GetText) () const;

    // 返回本对象中文本的哈希值(区分大小写)
    inline_ DWORD GetHash () const
    {
        return GetTextHash (GetText ());
    }

    // 返回本对象中文本的哈希值(不区分大小写)
    inline_ DWORD GetIHash () const
    {
        return GetTextIHash (GetText ());
    }

    // 返回文本长度
    INT_P GetLength () const;

    // 设置文本的新长度,如果小于原有文本长度,则将原有文本剪切到新长度,如果大于原有文本长度,则在尾部补充对应数目的空白字符.
    void SetLength (const INT_P npNewLength);

    // 重新分配本文本的空间,用所指定长度的指定字符填写文本内容.
    // 返回所分配文本空间的首地址.
    _MYS_TCHAR* InitWithChars (const INT_P npNumChars, const _MYS_TCHAR ch);

    // 返回本对象中是否为空文本
    inline_ BOOL_P IsEmpty () const
    {
        return (m_szConstText != NULL ? *m_szConstText == '\0' : m_mem.GetSize () <= (INT_P)sizeof (_MYS_TCHAR));
    }

    // 清空本对象的内容
    inline_ void Empty ()
    {
        m_szConstText = NULL;
        m_mem.Free ();
    }

    // 删除从指定字符索引位置开始的指定数目的字符数
    // 返回所实际删除的字符数
    INT_P RemoveChars (const INT_P npBeginIndex, INT_P npNumChars);

    // 返回两个文本内容是否相同(不区分大小写)
    inline_ BOOL_P IIsEqual (const _MYS_TCHAR* ps) const
    {
        ASSERT_R_STR (ps);
        return (_MYS_STRICMP (GetText (), ps) == 0);
    }
    inline_ BOOL_P IIsEqual (const _MY_STRING& str) const
    {
        return (_MYS_STRICMP (GetText (), str.GetText ()) == 0);
    }

    // 返回两个文本内容是否相同(区分大小写)
    inline_ BOOL_P IsEqual (const _MYS_TCHAR* ps) const
    {
        ASSERT_R_STR (ps);
        return (_MYS_STRCMP (GetText (), ps) == 0);
    }

    inline_ INT_P icompare (const _MYS_TCHAR* ps) const
    {
        ASSERT_R_STR (ps);
        return _MYS_STRICMP (GetText (), ps);
    }
    inline_ INT_P icompare (const _MY_STRING& str) const
    {
        return _MYS_STRICMP (GetText (), str.GetText ());
    }

    inline_ INT_P compare (const _MYS_TCHAR* ps) const
    {
        ASSERT_R_STR (ps);
        return _MYS_STRCMP (GetText (), ps);
    }
    inline_ INT_P compare (const _MY_STRING& str) const
    {
        return _MYS_STRCMP (GetText (), str.GetText ());
    }

    // blpCaseSensitive: 是否大小写敏感
    inline_ INT_P compare (const _MY_STRING& str, const BOOL_P blpCaseSensitive) const
    {
        return (blpCaseSensitive ? _MYS_STRCMP (GetText (), str.GetText ()) : _MYS_STRICMP (GetText (), str.GetText ()));
    }

    // 如果文本内容不以OS_PATH_CHAR结束,则加上去.
    inline_ void CheckAddPathChar ()
    {
        if (EndOf (OS_PATH_CHAR) == FALSE)
            AddChar (OS_PATH_CHAR);
    }

    inline_ BOOL operator== (const _MY_STRING& s) const
    {
        return (_MYS_STRCMP (GetText (), s.GetText ()) == 0);
    }
    inline_ BOOL operator!= (const _MY_STRING& s) const
    {
        return (_MYS_STRCMP (GetText (), s.GetText ()) != 0);
    }

    inline_ BOOL operator> (const _MY_STRING& s) const
    {
        return (_MYS_STRCMP (GetText (), s.GetText ()) > 0);
    }
    inline_ BOOL operator>= (const _MY_STRING& s) const
    {
        return (_MYS_STRCMP (GetText (), s.GetText ()) >= 0);
    }
    inline_ BOOL operator< (const _MY_STRING& s) const
    {
        return (_MYS_STRCMP (GetText (), s.GetText ()) < 0);
    }
    inline_ BOOL operator<= (const _MY_STRING& s) const
    {
        return (_MYS_STRCMP (GetText (), s.GetText ()) <= 0);
    }

    const _MY_STRING& operator= (const _MYS_TCHAR ch);
    const _MY_STRING& operator= (const _MYS_TCHAR* ps);
    const _MY_STRING& operator+= (const _MY_STRING& string);

    inline_ const _MY_STRING& operator+= (const _MYS_TCHAR ch)
    {
        AddChar (ch);
        return *this;
    }

    const _MY_STRING& operator+= (const _MYS_TCHAR* ps);

    void InsertChar (const INT_P npIndex, const _MYS_TCHAR ch);

    void AddChar (const _MYS_TCHAR ch);
    void AddChar (const _MYS_TCHAR ch, const INT_P npCount);

    void AddText (const _MYS_TCHAR* ps);
    void AddText (const _MYS_TCHAR* ps, const INT_P npLen);
    void CheckAddText (const _MYS_TCHAR* ps, INT_P npLen);  // 相比AddText,本方法处理了所指定文本中间存在零字符的情况.

    inline_ void AddText (const _MYS_OTHER_CHAR* ps, const INT_P npLen = -1)
    {
        ASSERT_R_STR2_NEG1 (ps, npLen);
        AddText (_MY_STRING (ps, npLen).GetText ());
    }

    inline_ void AddText (const _MY_STRING& str)
    {
        AddText (str.GetText ());
    }

    inline_ void AddManyText (const _MYS_TCHAR* ps, const INT_P npNumAdd)
    {
        for (INT_P npIndex = 0; npIndex < npNumAdd; npIndex++)
            AddText (ps);
    }

    inline_ void AddLine (const _MYS_TCHAR* ps)
    {
        AddText (ps);
        AddEmptyLine ();
    }

    void AddLowerText (const _MYS_TCHAR* ps);
    void AddLowerText (const _MYS_TCHAR* ps, const INT_P npLen);

    void AddUpperText (const _MYS_TCHAR* ps);
    void AddUpperText (const _MYS_TCHAR* ps, const INT_P npLen);

    // 加入多行文本,在每行的首部加入所指定数目的空格.
    //   npNumLeaderSpaces: 指定所欲在每行首部加入的空格数目,如果为负数,则为欲在每行首部删除的空格数目.
    void AddMutilLineTextWithLeaderSpaces (const _MYS_TCHAR* szMutilLineText, const INT_P npNumLeaderSpaces);
    inline_ void AddMutilLineTextWithLeaderSpaces (const _MY_STRING& str, const INT_P npNumLeaderSpaces)
    {
        AddMutilLineTextWithLeaderSpaces (str.GetText (), npNumLeaderSpaces);
    }

    inline_ void AddEmptyLine ()
    {
        AddText (_MYS_T ("\r\n"), 2);
    }

    // 在多行文本的每行首部添加指定数目的空格.
    void InsertLineBeginLeaderSpaces (const INT_P npNumLeaderSpaces);

    // 删除所指定索引位置处的指定数目的字符
    void RemoveChar (const INT_P npIndex, INT_P npLen = 1);

    // 删除多行文本中的所有空白行
    void RemoveAllSpaceLines ();

    // 如果文本以可以被删除的路径字符结束,则将该路径字符删除.
    // 返回处理后的本文本内容.
    const _MYS_TCHAR* RemoveEndPathChar ();

    void AddFormatText (const _MYS_TCHAR* szFormat, ...);
    void AddFormatTextWithLeaderSpaces (const INT_P npNumLeaderSpaces, const _MYS_TCHAR* szFormat, ...);  // 注意如果是多行文本,将在每行首部均添加指定数目的空格.
    void AddFormatLine (const _MYS_TCHAR* szFormat, ...);
    void AddFormatLineWithLeaderSpaces (const INT_P npNumLeaderSpaces, const _MYS_TCHAR* szFormat, ...);  // 注意如果是多行文本,将在每行首部均添加指定数目的空格.

    inline_ void InsertText (const INT_P npIndex, const _MYS_TCHAR* ps)
    {
        ASSERT_R_STR (ps);
        InsertText (npIndex, ps, _MYS_STRLEN (ps));
    }

    inline_ void InsertText (const INT_P npIndex, const _MY_STRING& str)
    {
        InsertText (npIndex, str.GetText ());
    }

    void InsertText (const INT_P npIndex, const _MYS_TCHAR* ps, const INT_P npLen);

    inline_ void InsertText (const INT_P npIndex, const _MYS_OTHER_CHAR* ps, const INT_P npLen = -1)
    {
        InsertText (npIndex, _MY_STRING (ps, npLen).GetText ());
    }

    void SetConstText (const _MYS_TCHAR* szConstText);

    inline_ void SetText (const _MY_STRING& str)
    {
        m_szConstText = str.m_szConstText;
        m_mem.CopyFrom (str.m_mem);
    }

    void _NAME_COMPILER_AGREED (SetText) (const _MYS_TCHAR* ps);
    void SetText (const _MYS_TCHAR* ps, const INT_P npLen);
    void CheckSetText (const _MYS_TCHAR* ps, INT_P npLen);  // 相比SetText,本方法处理了所指定文本中间存在零字符的情况.

    inline_ _MY_STRING& ReverseSetText (const _MYS_TCHAR* ps)
    {
        return ReverseSetText (ps, _MYS_STRLEN (ps));
    }
    _MY_STRING& ReverseSetText (const _MYS_TCHAR* ps, INT_P npLen);

    // npLen如果为-1,则加入全部文本.
    void SetText (const _MYS_OTHER_CHAR* ps, const INT_P npLen = -1);

    // 将长度为npLen的ps文本设置进本对象,但是跳过其中的所有控制类ASCII字符,并将制表符替换为空格.
    //   blpAllowLFChar: 是否允许换行符的存在
    void SetTextWithoutControlChars (const _MYS_TCHAR* ps, INT_P npLen, const BOOL_P blpAllowLFChar);

    inline_ void SetTextWithoutControlChars (const _MYS_TCHAR* szText, const BOOL_P blpAllowLFChar)
    {
        ASSERT_R_STR (szText);
        SetTextWithoutControlChars (szText, _MYS_STRLEN (szText), blpAllowLFChar);
    }

    // 将长度为npLen的ps文本设置进本对象,并将其中每个单独的换行符替换为回车换行两个字符.
    void SetTextReplaceLF2CRLF (const _MYS_TCHAR* ps, const INT_P npLen);
    inline_ void SetTextReplaceLF2CRLF (const _MYS_TCHAR* szText)
    {
        ASSERT_R_STR (szText);
        SetTextReplaceLF2CRLF (szText, _MYS_STRLEN (szText));
    }

    // 将长度为npLen的ps文本设置进本对象,并将其中每处回车换行两个字符均替换为一个换行符.
    void SetTextReplaceCRLF2LF (const _MYS_TCHAR* ps, const INT_P npLen);
    inline_ void SetTextReplaceCRLF2LF (const _MYS_TCHAR* szText)
    {
        ASSERT_R_STR (szText);
        SetTextReplaceCRLF2LF (szText, _MYS_STRLEN (szText));
    }

    // 将本文本中的所有控制字符替换为空格字符
    void ReplaceAllControlCharsToSpace ();

    inline_ const _MYS_OTHER_CHAR* GetOtherCodeText (CVolMem& memBuf) const
    {
    #ifdef _MY_WSTRING_IMPL
        return ::WStrToUtf8 (GetText (), GetLength (), memBuf);
    #else
        return ::Utf8ToWStr (GetText (), GetLength (), memBuf);
    #endif
    }

    virtual void GetDumpString (CVolString& strDump, INT nMaxDumpSize) override
    {
        strDump.SetText (GetText ());
    }

    virtual void LoadFromStream (CVolBaseInputStream& stream) override;
    virtual void SaveIntoStream (CVolBaseOutputStream& stream) override;

    inline_ friend CVolBaseInputStream& operator>> (CVolBaseInputStream& stream, _MY_STRING& str)
    {
        str.LoadFromStream (stream);
        return stream;
    }

    inline_ friend CVolBaseOutputStream& operator<< (CVolBaseOutputStream& stream, const _MY_STRING& str)
    {
        return str.VolSaveIntoStream (stream);
    }

    void AddFloatText (const FLOAT flt);
    void AddDoubleText (const DOUBLE db);
    void AddIntText (const INT n);
    void AddDWordText (const DWORD dw);
    void AddInt64Text (const INT64 n64);
    void AddUInt64Text (const UINT64 u64);
    void AddIntPText (const INT_P np);
    void AddUIntPText (const UINT_P up);

    inline_ void SetCharText (const _MYS_TCHAR ch)  {  Empty ();  AddChar (ch);         }
    inline_ void SetFloatText (const FLOAT flt)     {  Empty ();  AddFloatText (flt);   }
    inline_ void SetDoubleText (const DOUBLE db)    {  Empty ();  AddDoubleText (db);   }
    inline_ void SetIntText (const INT n)           {  Empty ();  AddIntText (n);       }
    inline_ void SetDWordText (const DWORD dw)      {  Empty ();  AddDWordText (dw);    }
    inline_ void SetInt64Text (const INT64 n64)     {  Empty ();  AddInt64Text (n64);   }
    inline_ void SetUInt64Text (const UINT64 u64)   {  Empty ();  AddUInt64Text (u64);  }
    inline_ void SetIntPText (const INT_P np)       {  Empty ();  AddIntPText (np);     }
    inline_ void SetUIntPText (const UINT_P up)     {  Empty ();  AddUIntPText (up);    }

    inline_ void SetValueText (const _MYS_TCHAR* ps)        {  SetText (ps);           }
    inline_ void SetValueText (const _MYS_OTHER_CHAR* ps)   {  SetText (ps);           }
#if (defined (_MY_WSTRING_IMPL) && defined (_UNICODE))  // 为实现宽文本对象且为编译Unicode版本?
    inline_ void SetValueText (const S_BYTE sb)             {  SetIntText ((INT)sb);   }
#endif
    inline_ void SetValueText (const SHORT sht)             {  SetIntText ((INT)sht);  }
    inline_ void SetValueText (const _MYS_TCHAR ch)         {  SetCharText (ch);       }
    inline_ void SetValueText (const INT n)                 {  SetIntText (n);         }
    inline_ void SetValueText (const INT64 n64)             {  SetInt64Text (n64);     }
    inline_ void SetValueText (const FLOAT flt)             {  SetFloatText (flt);     }
    inline_ void SetValueText (const DOUBLE db)             {  SetDoubleText (db);     }

    // 取子文本
    _MY_STRING Left (INT_P npCount) const;
    _MY_STRING Right (INT_P npCount) const;
    _MY_STRING Middle (INT_P npIndex, INT_P npCount) const;

    // 大小写转换
    _MY_STRING& MakeUpper ();
    _MY_STRING& MakeLower ();
    void MakeFirstLetterLower ();
    void MakeFirstLetterUpper ();

    // 清除文本的左右空白
    _MY_STRING& TrimLeft ();
    _MY_STRING& TrimRight ();

    // 清除文本中的全部空白
    _MY_STRING& TrimAllSpaces ();
        ;
    // 清除文本的首尾空白
    inline_ _MY_STRING& TrimAll ()
    {
        TrimLeft ();
        TrimRight ();
        return *this;
    }

    inline_ _MYS_TCHAR GetCharAt (const INT_P npCharIndex) const
    {
        ASSERT (npCharIndex >= 0 && npCharIndex < GetLength ());
        return GetText () [npCharIndex];
    }

    inline_ INT_P FindChar (const _MYS_TCHAR ch) const
    {
        return FindChar (ch, 0);
    }

    inline_ INT_P FindChar (const _MYS_TCHAR ch, const INT_P npFindBeginIndex) const
    {
        ASSERT (npFindBeginIndex >= 0 && npFindBeginIndex <= GetLength ());

        const _MYS_TCHAR* psBegin = GetText ();
        const _MYS_TCHAR* ps = _MYS_STRCHR (psBegin + npFindBeginIndex, ch);

        return (ps == NULL ? -1 : ps - psBegin);
    }

    inline_ INT_P ReverseFindChar (const _MYS_TCHAR ch) const
    {
        const _MYS_TCHAR* psBegin = GetText ();
        const _MYS_TCHAR* ps = _MYS_STRRCHR (psBegin, ch);

        return (ps == NULL ? -1 : ps - psBegin);
    }

    inline_ INT_P MFindText (const _MYS_TCHAR* szText) const
    {
        const _MYS_TCHAR* psBegin = GetText ();
        const _MYS_TCHAR* ps = _MYS_STRSTR (psBegin, szText);

        return (ps == NULL ? -1 : ps - psBegin);
    }

    // 查找所指定的文本,成功返回其索引位置,失败返回-1.
    //   szSearch: 所欲查找的文本
    //   npBeginIndex: 提供起始查找的索引位置,小于等于文本长度,如果blpReverseFind为真且小于0表示从文本尾部开始查找.
    //   blpCaseInsensitive: 是否不区分大小写
    //   blpReverseFind: 是否为逆向查找
    INT_P SearchText (const _MYS_TCHAR* szSearch, INT_P npBeginIndex, const BOOL_P blpCaseInsensitive, const BOOL_P blpReverseFind);

    // 将所指定部分的文本替换为指定文本
    void MReplaceText (INT_P npBeginIndex, INT_P npReplaceLen, const _MYS_TCHAR* szReplaceText);

    // 将文本中所有指定子文本替换为指定文本
    //   szFindText: 需要被替换的子文本
    //   szReplaceText: 用作替换的文本
    //   npBeginIndex: 起始替换索引位置
    //   npReplaceTimes: 替换次数,为-1表示替换所有匹配子文本.
    //   blpCaseInsensitive: 是否不区分大小写
    void ReplaceSubText (const _MYS_TCHAR* szFindText, const _MYS_TCHAR* szReplaceText,
            INT_P npBeginIndex, INT_P npReplaceTimes, const BOOL_P blpCaseInsensitive);

    // 返回是否产生了实际替换
    BOOL_P Replace (const _MYS_TCHAR* szFindText, const _MYS_TCHAR* szReplaceText);
    
    // 返回是否产生了实际替换
    BOOL_P Replace (const INT_P npBeginCharIndex, const _MYS_TCHAR chFind, const _MYS_TCHAR chReplace);
    inline_ BOOL_P Replace (const _MYS_TCHAR chFind, const _MYS_TCHAR chReplace)
    {
        return Replace (0, chFind, chReplace);
    }

    // blpCaseSensitive: 是否区分大小写
    inline_ BOOL_P LeadOf (const _MYS_TCHAR ch, const BOOL_P blpCaseSensitive) const
    {
        return (blpCaseSensitive ? LeadOf (ch) : ILeadOf (ch));
    }
    inline_ BOOL_P LeadOf (const _MYS_TCHAR ch) const
    {
        return ::LeadOf (GetText (), ch);
    }
    inline_ BOOL_P ILeadOf (const _MYS_TCHAR ch) const
    {
        return ::ILeadOf (GetText (), ch);
    }

    // blpCaseSensitive: 是否区分大小写
    inline_ BOOL_P LeadOf (const _MYS_TCHAR* szLeaderOf, const BOOL_P blpCaseSensitive) const
    {
        return (blpCaseSensitive ? LeadOf (szLeaderOf) : ILeadOf (szLeaderOf));
    }
    inline_ BOOL_P LeadOf (const _MYS_TCHAR* szLeaderOf) const
    {
        return ::LeadOf (GetText (), szLeaderOf);
    }
    inline_ BOOL_P ILeadOf (const _MYS_TCHAR* szLeaderOf) const
    {
        return ::ILeadOf (GetText (), szLeaderOf);
    }

    inline_ BOOL_P EndOf (const _MYS_TCHAR ch, const BOOL_P blpCaseSensitive) const
    {
        return (blpCaseSensitive ? EndOf (ch) : IEndOf (ch));
    }
    inline_ BOOL_P EndOf (const _MYS_TCHAR ch) const
    {
        const INT_P npLength = GetLength ();
        return (npLength > 0 && GetText () [npLength - 1] == ch);
    }
    inline_ BOOL_P IEndOf (const _MYS_TCHAR ch) const
    {
        const INT_P npLength = GetLength ();
        return (npLength > 0 && ToUpperCase (GetText () [npLength - 1]) == ToUpperCase (ch));
    }

    inline_ BOOL_P EndOf (const _MYS_TCHAR* szEndOf, const BOOL_P blpCaseSensitive) const
    {
        return (blpCaseSensitive ? EndOf (szEndOf) : IEndOf (szEndOf));
    }
    inline_ BOOL_P EndOf (const _MYS_TCHAR* szEndOf) const
    {
        return ::EndOf (GetText (), szEndOf);
    }
    inline_ BOOL_P IEndOf (const _MYS_TCHAR* szEndOf) const
    {
        return ::IEndOf (GetText (), szEndOf);
    }

    inline_ _MYS_TCHAR GetLastChar () const
    {
        const INT_P npLength = GetLength ();
        return (npLength > 0 ? GetText () [npLength - 1] : '\0');
    }

    _MY_STRING& Format (const _MYS_TCHAR* szFormat, ...);
    void FormatV (const _MYS_TCHAR* szFormat, va_list argList);

    // 如果当前文本不以换行符结束,则添加一个"\r\n"文本,否则不添加.
    void CheckAddCRLF ();

#if (defined (_MY_WSTRING_IMPL) && defined (_UNICODE))  // 为实现宽文本对象且为编译Unicode版本?
    // 将文本中所有的半角英文字符转换为对应的全角中文字符,本方法不会影响到文本内容的长度.
    _MY_STRING& BJ2QJ ();

    // 将文本中所有的全角中文字符转换为对应的半角英文字符.本方法不会影响到文本内容的长度.
    _MY_STRING& QJ2BJ ();
#endif

    // 将所指定二进制数据进行Base64编码后置入本文本对象中.
    //   pData, npDataSize: 所欲编码的二进制数据及其尺寸
    //   npMaxLineLen: 每行编码文本的最大字符数,小于0表示无限制,等于0表示使用默认每行字符数(76).
    //   npEncodeType: 编码方式: 0:标准Base64编码; 1:URL专用Base64编码; 2:正则专用Base64编码
    _MY_STRING& EncodeBase64 (const BYTE* pData, const INT_P npDataSize, INT_P npMaxLineLen, const INT_P npEncodeType);
    inline_ _MY_STRING& EncodeBase64 (const CVolMem& memData, INT_P npMaxLineLen, const INT_P npEncodeType)
    {
        return EncodeBase64 (memData.GetPtr (), memData.GetSize (), npMaxLineLen, npEncodeType);
    }

    // 将所指定的Base64编码文本解码后置入所指定的内存对象中
    //   psSrc, npSrcLen: Base64编码文本及其长度,如果npSrcLen小于0则自动获取其长度.
    //   memResult: 用作存放解码结果.
    //   npEncodeType: 编码方式: 0:标准Base64编码; 1:URL专用Base64编码; 2:正则专用Base64编码
    static CVolMem& sDecodeBase64 (const _MYS_TCHAR* psSrc, INT_P npSrcLen, CVolMem& memResult, const INT_P npEncodeType);
    inline_ CVolMem& DecodeBase64 (CVolMem& memResult, const INT_P npEncodeType)
    {
        return sDecodeBase64 (GetText (), GetLength (), memResult, npEncodeType);
    }

    // 将所指定二进制数据进行Quoted-Printable编码后置入本文本对象中.
    //   pData, npDataSize: 所欲编码的二进制数据及其尺寸
    //   npMaxLineLen: 每行编码文本的最大字符数,小于0表示无限制,等于0表示使用默认每行字符数(76).
    _MY_STRING& EncodeQuoted (const BYTE* pData, const INT_P npDataSize, INT_P npMaxLineLen);
    inline_ _MY_STRING& EncodeQuoted (const CVolMem& memData, INT_P npMaxLineLen)
    {
        return EncodeQuoted (memData.GetPtr (), memData.GetSize (), npMaxLineLen);
    }

    // 将所指定的Quoted-Printable编码文本解码后置入所指定的内存对象中
    //   psSrc, npSrcLen: Quoted-Printable编码文本及其长度,如果npSrcLen小于0则自动获取其长度.
    //   memResult: 用作存放解码结果.
    static CVolMem& sDecodeQuoted (const _MYS_TCHAR* psSrc, INT_P npSrcLen, CVolMem& memResult);
    inline_ CVolMem& DecodeQuoted (CVolMem& memResult)
    {
        return sDecodeQuoted (GetText (), GetLength (), memResult);
    }

    // 从文件中读入并返回指定尺寸的文本内容,读取失败将返回空文本(注意正常情况下也可能返回空文本).
    // npReadDataSize为-1表示读入全部
    // pblpReadSucceeded如果不为NULL,则在其中返回是否读入成功.
    _MY_STRING& ReadFromFile (const TCHAR* szFileName, INT_P npReadDataSize, VOL_STRING_ENCODE_TYPE enEncodeType, BOOL_P* pblpReadSucceeded = NULL);

    // 将指定长度的文本写入文件中,成功返回真,失败返回假.
    //   npWriteStrLength: 所欲写出的字符数目,为-1表示写入全部.
    BOOL_P WriteIntoFile (const TCHAR* szFileName, INT_P npWriteStrLength, const VOL_STRING_ENCODE_TYPE enEncodeType) const;

    // 取所指定日期时间的格式文本. 成功返回格式文本,失败返回空文本.
    _MY_STRING& FormatDateTime (DATE dt, const TCHAR* szFormat);

protected:
    static INT_P sCalcMaxLen (const _MYS_TCHAR* szFormat, va_list argList);
    static _MYS_TCHAR sGetBase64EncodeChar (BYTE bt, const INT_P npEncodeType);
    static UINT_P sGetBase64DecodeByte (_MYS_TCHAR ch, const INT_P npEncodeType);
    CVolMem& CheckConvertConstText ();

public:
    const _MYS_TCHAR* _NAME_COMPILER_AGREED (m_szConstText);  // 用作记录常量文本,为NULL表示无.
    CVolMem _NAME_COMPILER_AGREED (m_mem);  // 仅当m_szConstText为NULL时有效
};

_MY_STRING operator+ (const _MY_STRING& string1, const _MY_STRING& string2);
_MY_STRING operator+ (const _MY_STRING& string, const _MYS_TCHAR ch);
_MY_STRING operator+ (const _MY_STRING& string, const _MYS_TCHAR* ps);
_MY_STRING operator+ (const _MYS_TCHAR* ps, const _MY_STRING& string);
_MY_STRING operator+ (const _MYS_TCHAR ch, const _MY_STRING& string);

inline_ BOOL operator== (const _MY_STRING& s1, const _MYS_TCHAR* s2)
{
    ASSERT_R_STR (s2);
    return (_MYS_STRCMP (s1.GetText (), s2) == 0);
}

inline_ BOOL operator!= (const _MY_STRING& s1, const _MYS_TCHAR* s2)
{
    ASSERT_R_STR (s2);
    return (_MYS_STRCMP (s1.GetText (), s2) != 0);
}

inline_ BOOL operator== (const _MYS_TCHAR* s1, const _MY_STRING& s2)
{
    ASSERT_R_STR (s1);
    return (_MYS_STRCMP (s2.GetText (), s1) == 0);
}

inline_ BOOL operator!= (const _MYS_TCHAR* s1, const _MY_STRING& s2)
{
    ASSERT_R_STR (s1);
    return (_MYS_STRCMP (s2.GetText (), s1) != 0);
}

//----------------------------------------------------------------------------------

// 火山常量文本对象类
class _MY_CONST_STRING : public _MY_STRING
{
    DECLARE_GLOBAL_EMPTY_VOL_CLASS_NOT_OVR_COMP (_MY_CONST_STRING)
     
public:
    inline_ _MY_CONST_STRING ()
    {
    }

    inline_ _MY_CONST_STRING (const _MYS_TCHAR* szConstText) : _MY_STRING ()
    {
        m_szConstText = szConstText;
    }
};

//   两者数据尺寸必须一致,否则将导致两者所定义的数组尺寸不一致,导致直接使用
// 索引值遍历成员出错(譬如基于_MY_STRING去遍历一个_MY_CONST_STRING数组).
COMPILE_TIME_ASSERT (sizeof (_MY_CONST_STRING) == sizeof (_MY_STRING));

//----------------------------------------------------------------------------------

// 携带有文本HASH值(区分大小写)的文本对象类
class _MY_STRING_WITH_HASH : public CVolCommonBase
{
public:
    inline_ _MY_STRING_WITH_HASH  ()
    {
        m_dwHash = 0;
    }

    inline_ _MY_STRING_WITH_HASH (const _MYS_TCHAR* szText)
    {
        SetText (szText);
    }

    inline_ _MY_STRING_WITH_HASH (const _MYS_TCHAR* psText, const INT_P npLength)
    {
        SetText (psText, npLength);
    }

    inline_ _MY_STRING_WITH_HASH (const _MY_STRING_WITH_HASH& strWithHash)
    {
        SetText (strWithHash);
    }

public:
    inline_ BOOL_P IsEmpty () const
    {
        return m_str.IsEmpty ();
    }

    inline_ void Empty ()
    {
        m_str.Empty ();
        m_dwHash = 0;
    }

    inline_ void SetText (const _MYS_TCHAR* psText, const INT_P npLength)
    {
        m_str.SetText (psText, npLength);
        UpdateHash ();
    }

    inline_ void SetText (const _MYS_TCHAR* szText)
    {
        m_str.SetText (szText);
        UpdateHash ();
    }

    inline_ void SetText (const _MY_STRING_WITH_HASH& strWithHash)
    {
        m_str.SetText (strWithHash.m_str);
        m_dwHash = strWithHash.m_dwHash;
    }

    inline_ void SetTextWithHash (const _MYS_TCHAR* szText, const DWORD dwTextHash)
    {
        ASSERT (GetTextHash (szText) == dwTextHash);

        m_str.SetText (szText);
        m_dwHash = dwTextHash;
    }

    inline_ const _MYS_TCHAR* GetText () const
    {
        return m_str.GetText ();
    }

    inline_ DWORD GetHash () const
    {
        return m_dwHash;
    }

    inline_ INT_P GetTextLength () const
    {
        return m_str.GetLength ();
    }

    inline_ const _MY_STRING& GetString () const
    {
        return m_str;
    }

    inline_ _MY_STRING& GetString ()
    {
        return m_str;
    }

    // 如果直接修改了文本内容,必须调用此方法更新HASH值
    inline_ void UpdateHash ()
    {
        m_dwHash = GetTextHash (m_str.GetText ());
    }

    //----------------------------------------------------------------------

    inline_ BOOL_P IsEqual (const _MYS_TCHAR* szText) const
    {
        return (m_str.compare (szText) == 0);
    }

    inline_ BOOL_P IsEqual (const _MYS_TCHAR* szText, const DWORD dwTextHash) const
    {
        return (dwTextHash == m_dwHash && m_str.compare (szText) == 0);
    }

    inline_ BOOL_P IsEqual (const _MY_STRING_WITH_HASH& strWithHash) const
    {
        return (strWithHash.m_dwHash == m_dwHash &&
                m_str.compare (strWithHash.GetText ()) == 0);
    }

    friend CVolBaseInputStream& operator>> (CVolBaseInputStream& stream, _MY_STRING_WITH_HASH& strWithHash);
    friend CVolBaseOutputStream& operator<< (CVolBaseOutputStream& stream, const _MY_STRING_WITH_HASH& strWithHash);

protected:
    _MY_STRING m_str;
    DWORD m_dwHash;
};

//----------------------------------------------------------------------------------

// 携带有文本HASH值(不区分大小写)的文本对象类
class _MY_STRING_WITH_IHASH : public CVolCommonBase
{
public:
    inline_ _MY_STRING_WITH_IHASH  ()
    {
        m_dwIHash = 0;
    }

    inline_ _MY_STRING_WITH_IHASH (const _MYS_TCHAR* szText)
    {
        SetText (szText);
    }

    inline_ _MY_STRING_WITH_IHASH (const _MYS_TCHAR* psText, const INT_P npLength)
    {
        SetText (psText, npLength);
    }

    inline_ _MY_STRING_WITH_IHASH (const _MY_STRING_WITH_IHASH& strWithIHash)
    {
        SetText (strWithIHash);
    }

public:
    inline_ BOOL_P IsEmpty () const
    {
        return m_str.IsEmpty ();
    }

    inline_ void Empty ()
    {
        m_str.Empty ();
        m_dwIHash = 0;
    }

    inline_ void SetText (const _MYS_TCHAR* szText)
    {
        m_str.SetText (szText);
        UpdateIHash ();
    }

    inline_ void SetText (const _MYS_TCHAR* psText, const INT_P npLength)
    {
        m_str.SetText (psText, npLength);
        UpdateIHash ();
    }

    inline_ void SetText (const _MY_STRING_WITH_IHASH& strWithIHash)
    {
        m_str.SetText (strWithIHash.m_str);
        m_dwIHash = strWithIHash.m_dwIHash;
    }

    inline_ void SetTextWithIHash (const _MYS_TCHAR* szText, const DWORD dwTextIHash)
    {
        ASSERT (GetTextIHash (szText) == dwTextIHash);

        m_str.SetText (szText);
        m_dwIHash = dwTextIHash;
    }

    inline_ const _MYS_TCHAR* GetText () const
    {
        return m_str.GetText ();
    }

    inline_ DWORD GetIHash () const
    {
        return m_dwIHash;
    }

    inline_ INT_P GetTextLength () const
    {
        return m_str.GetLength ();
    }

    inline_ const _MY_STRING& GetString () const
    {
        return m_str;
    }

    inline_ _MY_STRING& GetString ()
    {
        return m_str;
    }

    // 如果直接修改了文本内容,必须调用此方法更新IHASH值
    inline_ void UpdateIHash ()
    {
        m_dwIHash = GetTextIHash (m_str.GetText ());
    }

    //----------------------------------------------------------------------

    inline_ BOOL_P IsEqual (const _MYS_TCHAR* szText) const
    {
        return (m_str.icompare (szText) == 0);
    }

    inline_ BOOL_P IsEqual (const _MYS_TCHAR* szText, const DWORD dwTextIHash) const
    {
        return (dwTextIHash == m_dwIHash && m_str.icompare (szText) == 0);
    }

    inline_ BOOL_P IsEqual (const _MY_STRING_WITH_IHASH& strWithIHash) const
    {
        return (strWithIHash.m_dwIHash == m_dwIHash &&
                m_str.icompare (strWithIHash.GetText ()) == 0);
    }

    friend CVolBaseInputStream& operator>> (CVolBaseInputStream& stream, _MY_STRING_WITH_IHASH& strWithIHash);
    friend CVolBaseOutputStream& operator<< (CVolBaseOutputStream& stream, const _MY_STRING_WITH_IHASH& strWithIHash);

protected:
    _MY_STRING m_str;
    DWORD m_dwIHash;
};

//----------------------------------------------------------------------------------

// 具有内部缓冲区的文本对象类
class _MY_BUF_STRING : public CVolCommonBase
{
public:
    inline_ _MY_BUF_STRING ()
    {
        m_acBuf [0] = '\0';
    }

    inline_ _MY_BUF_STRING (const _MYS_TCHAR* szText)
    {
        SetText (szText);
    }

    inline_ _MY_BUF_STRING (const _MYS_TCHAR* psText, const INT_P npLength)
    {
        SetText (psText, npLength);
    }

    inline_ _MY_BUF_STRING (const _MY_BUF_STRING& str)
    {
        SetText (str);
    }

public:
    inline_ BOOL_P IsEmpty () const
    {
        return (m_str.IsEmpty () && m_acBuf [0] == '\0');
    }

    inline_ void Empty ()
    {
        m_str.Empty ();
        m_acBuf [0] = '\0';
    }

    void SetText (const _MYS_TCHAR* szText);
    void SetText (const _MYS_TCHAR* psText, const INT_P npLength);

    inline_ void SetText (const _MY_BUF_STRING& str)
    {
        SetText (str.GetText ());
    }

    inline_ const _MYS_TCHAR* GetText () const
    {
        return (m_str.IsEmpty () ? m_acBuf : m_str.GetText ());
    }

    inline_ INT_P GetTextLength () const
    {
        return (m_str.IsEmpty () ? _MYS_STRLEN (m_acBuf) : m_str.GetLength ());
    }

protected:
    _MY_STRING m_str;  // 如果不为空,则本对象的内容即为此文本对象的内容,否则为m_acBuf缓冲区的内容.
    _MYS_TCHAR m_acBuf [256];
};
