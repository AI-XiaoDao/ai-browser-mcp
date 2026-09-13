
// Copyright (C) Recursion Company. All rights reserved.

// _NAME_COMPILER_AGREED,本文件中的所有名称均被编译器所约定.

#ifndef __VOL_DECL_H__
#define __VOL_DECL_H__

// 定义Unicode宏
// 注意: 本头文件不支持多字节集,如果定义了Unicode宏,则使用Unicode字符集,否则使用UTF8字符集.
#ifdef UNICODE
    #ifndef _UNICODE
        #define _UNICODE
    #endif
#endif
#ifdef _UNICODE
    #ifndef UNICODE
        #define UNICODE
    #endif
#endif

//-----------------------------------------------------------------------------  常用系统头文件

#include <stdlib.h>
#include <stdio.h>
#include <locale.h>
#include <stddef.h>
#include <stdarg.h>
#include <math.h>
#include <float.h>
#include <assert.h>
#include <direct.h>

// 检查当前编译器
#if defined (_MSC_VER)
    #define __MS_CPP__  // VC++
#elif !defined (__GNU_CPP__)
    #define __GNU_CPP__  // 默认为g++
#endif

//-----------------------------------------------------------------------------  当前目标平台

// 根据预定义宏确定windows平台的位数
#if (defined (_WIN64) || defined (WIN64))
    #ifndef _PF_WIN64
        #define _PF_WIN64
    #endif
#elif (defined (_WIN32) || defined (WIN32))
    #ifndef _PF_WIN32
        #define _PF_WIN32
    #endif
#endif

// 获取目标平台位数
#if (defined (_PF_WIN64) || defined (_PF_LINUX64))  // 64位目标平台?
    #ifndef _PF_64_BITS
        #define _PF_64_BITS  // 定义64位目标平台标志宏
    #endif
#elif (defined (_PF_WIN32) || defined (_PF_LINUX32))
    #ifndef _PF_32_BITS
        #define _PF_32_BITS  // 定义32位目标平台宏
    #endif
#else
    #error "Unknown target platform!"  // 未知目标平台
#endif

// 获取目标平台类型
#if (defined (_PF_WIN32) || defined (_PF_WIN64))
    #ifndef _PF_WINDOWS
        #define _PF_WINDOWS
    #endif
#elif (defined (_PF_LINUX32) || defined (_PF_LINUX64))
    #ifndef _PF_LINUX
        #define _PF_LINUX
    #endif
#endif

// 检查所定义平台有效性
#if ((defined (_PF_WINDOWS) && defined (_PF_LINUX)) || (defined (_PF_64_BITS) && defined (_PF_32_BITS)))
    #error Wrong target platform!
#elif ((!defined (_PF_WINDOWS) && !defined (_PF_LINUX)) || (!defined (_PF_64_BITS) && !defined (_PF_32_BITS)))
    #error Wrong target platform!
#endif

//-----------------------------------------------------------------------------  引入平台相关系统头文件

#if defined (_PF_WINDOWS)
    #pragma warning(disable : 4996)  // 禁止报告类似"'_swprintf': This function or variable may be unsafe. Consider using _swprintf_s instead"错误
    #pragma warning(disable : 4312)  // 禁止报告检测64位可移植性问题警告
    //   The variable FD_SETSIZE determines the maximum number of descriptors in a set.
    // The default value of FD_SETSIZE is 64, which can be modified by defining FD_SETSIZE
    // to another value before including Winsock2.h.
    #ifndef FD_SETSIZE
        #define FD_SETSIZE  1024
    #endif
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #include <windows.h>
    #include <time.h>
    #include <tchar.h>
    #include <commctrl.h>
    #include <Mmsystem.h>
    #include <shellapi.h>
    #include <shlobj.h>
#elif defined (_PF_LINUX)
    #include <wchar.h>
    #include <sys/types.h>
    #include <sys/time.h>
    #include <sys/stat.h>
    #include <sys/wait.h>
    #include <dlfcn.h>
    #include <unistd.h>
    #include <pthread.h>
    #include <string.h>
    #include <semaphore.h>
#endif

//-----------------------------------------------------------------------------  数据类型定义

typedef double DOUBLE;
typedef ptrdiff_t INT_P;
typedef size_t UINT_P;
typedef INT_P BOOL_P;
typedef char U8CHAR;  // UTF8字符
typedef signed char S_BYTE;  // 有符号字节

#ifdef _PF_LINUX
    typedef wchar_t WCHAR;  // 注意Linux系统和Windows系统的WCHAR尺寸不一致
    #ifdef _UNICODE
        typedef WCHAR TCHAR;
    #else
        typedef U8CHAR TCHAR;
    #endif
    typedef unsigned char BYTE;
    typedef short SHORT;
    typedef unsigned short WORD;
    typedef int INT;
    typedef unsigned int DWORD;
    typedef unsigned int UINT;
    typedef int BOOL;
    typedef float FLOAT;
    typedef long long INT64;
    typedef unsigned long long UINT64;
    typedef DWORD COLORREF;
    typedef void* HANDLE;
#endif

typedef const U8CHAR* P_CU8STR;
typedef U8CHAR* P_U8STR;
typedef const WCHAR* P_CWSTR;
typedef WCHAR* P_WSTR;
typedef const TCHAR* P_CTSTR;
typedef TCHAR* P_TSTR;

typedef void* VOID_PTR;
typedef const void* VOID_CPTR;
typedef void (*VOID_FUNC) ();  // A standard procedure call  // _NAME_COMPILER_AGREED
typedef UINT_P H_LIB;

//-----------------------------------------------------------------------------  数据类型值相关

#undef _VOL_SBYTE_MIN
#undef _VOL_SBYTE_MAX
#undef _VOL_BYTE_MAX
#undef _VOL_SHRT_MIN
#undef _VOL_SHRT_MAX
#undef _VOL_USHRT_MAX
#undef _VOL_INT_MIN
#undef _VOL_INT_MAX
#undef _VOL_WORD_MAX
#undef _VOL_DWORD_MAX
#undef _VOL_UINT_MAX
#undef _VOL_MAX_FLOAT
#undef _VOL_MIN_FLOAT
#undef _VOL_INT64_MIN
#undef _VOL_INT64_MAX
#undef _VOL_UINT64_MAX

#define _VOL_SBYTE_MIN   (-128)
#define _VOL_SBYTE_MAX   127
#define _VOL_BYTE_MAX    0xFF
#define _VOL_SHRT_MIN    (-32768)
#define _VOL_SHRT_MAX    32767
#define _VOL_USHRT_MAX   0xFFFF
#define _VOL_INT_MIN     (-2147483647 - 1)
#define _VOL_INT_MAX     2147483647
#define _VOL_WORD_MAX    0xFFFF
#define _VOL_DWORD_MAX   0xFFFFFFFF
#define _VOL_UINT_MAX    0xFFFFFFFF
#define _VOL_MAX_FLOAT   FLT_MAX
#define _VOL_MIN_FLOAT   (-FLT_MAX)
#define _VOL_INT64_MIN   LLONG_MIN
#define _VOL_INT64_MAX   LLONG_MAX
#define _VOL_UINT64_MAX  ULLONG_MAX

// 最小和最大日期时间值
#define _VOL_MIN_DATE  -657434  // about year 100
#define _VOL_MAX_DATE  2958465  // about year 9999

// INT_P和UINT_P类型的最大和最小值:
#ifdef _PF_64_BITS  // 64位目标平台?
    #define _VOL_INT_P_MIN   _VOL_INT64_MIN
    #define _VOL_INT_P_MAX   _VOL_INT64_MAX
    #define _VOL_UINT_P_MAX  _VOL_UINT64_MAX
#else
    #define _VOL_INT_P_MIN   _VOL_INT_MIN
    #define _VOL_INT_P_MAX   _VOL_INT_MAX
    #define _VOL_UINT_P_MAX  _VOL_UINT_MAX
#endif

#ifndef TRUE
    #define TRUE  1
#endif
#ifndef FALSE
    #define FALSE  0
#endif

//-----------------------------------------------------------------------------  Unicode相关宏

#ifdef _PF_LINUX
    #define _wtoi  (int)wcstol
    #define _wtof  wcstof

    #ifdef _UNICODE

        #define _T(t)           L ## t
        #define _TF_S           _T ("%ls")  // 定义用作TCHAR字符串的printf格式符unicode文本

        #define _putts(t)       fputws ((t), stdout)
        #define _fputts         fputws
        #define _tprintf        wprintf
        #define _ftprintf       fwprintf
        #define _stprintf       swprintf
        #define _vtprintf       vwprintf
        #define _vftprintf      vfwprintf
        #define _vstprintf      vswprintf
        #define _vsctprintf     _vscwprintf
        #define _tscanf         wscanf
        #define _ftscanf        fwscanf
        #define _stscanf        swscanf

        #define _tcstod         wcstod
        #define _tcstol         wcstol
        #define _tcstoul        wcstoul
        #define _ttof           wcstof
        #define _tstof          wcstof
        #define _tstol          wcstol
        #define _tstoi          (int)wcstol
        #define _ttoi           (int)wcstol

        #define _tcscat         wcscat
        #define _tcschr         wcschr
        #define _tcsrchr        wcsrchr
        #define _tcscpy         wcscpy
        #define _tcsncpy        wcsncpy
        #define _tcsstr         wcsstr
        #define _tcstok         wcstok
        #define _tcslen         wcslen
        #define _tcsnlen        wcsnlen
        #define _tcsxfrm        wcsxfrm
        #define _tcscmp         wcscmp
        #define _tcsicmp        wcscasecmp
        #define _tcsncmp        wcsncmp
        #define _tcsnicmp       wcsncasecmp
        #define _tcsftime       wcsftime

    #else

        #define _T(t)           t
        #define _TF_S           _T ("%s")  // 定义用作TCHAR字符串的printf格式符unicode文本

        #define _putts          puts
        #define _fputts         fputs
        #define _tprintf        printf
        #define _ftprintf       fprintf
        #define _stprintf       sprintf
        #define _vtprintf       vprintf
        #define _vftprintf      vfprintf
        #define _vstprintf      vsprintf
        #define _vsctprintf     _vscprintf
        #define _tscanf         scanf
        #define _ftscanf        fscanf
        #define _stscanf        sscanf

        #define _tcstod         strtod
        #define _tcstol         strtol
        #define _tcstoul        strtoul
        #define _ttof           atof
        #define _tstof          atof
        #define _tstol          atol
        #define _tstoi          atoi
        #define _ttoi           atoi

        #define _tcscat         strcat
        #define _tcschr         strchr
        #define _tcsrchr        strrchr
        #define _tcscpy         strcpy
        #define _tcsncpy        strncpy
        #define _tcsstr         strstr
        #define _tcstok         strtok
        #define _tcslen         strlen
        #define _tcsnlen        strnlen
        #define _tcsxfrm        strxfrm
        #define _tcscmp         strcmp
        #define _tcsicmp        strcasecmp
        #define _tcsncmp        strncmp
        #define _tcsnicmp       strncasecmp
        #define _tcsftime       strftime

    #endif
#else

    #define _TF_S  _T ("%s")  // 定义用作TCHAR字符串的printf格式符unicode文本

#endif

// 定义用作INT_P和UINT_P类型的printf格式符文本
#ifdef _PF_64_BITS  // 64位目标平台?
    #define _TF_NP  _T ("%I64d")
    #define _TF_UP  _T ("%I64u")
    #define _TF_HP  _T ("%I64X")
    #define _F_NP   "%I64d"
    #define _F_UP   "%I64u"
    #define _F_HP   "%I64X"
#else
    #define _TF_NP  _T ("%d")
    #define _TF_UP  _T ("%u")
    #define _TF_HP  _T ("%X")
    #define _F_NP   "%d"
    #define _F_UP   "%u"
    #define _F_HP   "%X"
#endif

//-----------------------------------------------------------------------------  信息输出

// 输出正常信息
#define PMSG0(s)                   _fputts ((s), stdout)
#define PMSG1(fmt,s1)              _ftprintf (stdout, (fmt), (s1))
#define PMSG2(fmt,s1,s2)           _ftprintf (stdout, (fmt), (s1), (s2))
#define PMSG3(fmt,s1,s2,s3)        _ftprintf (stdout, (fmt), (s1), (s2), (s3))
#define PMSG4(fmt,s1,s2,s3,s4)     _ftprintf (stdout, (fmt), (s1), (s2), (s3), (s4))
#define PMSG5(fmt,s1,s2,s3,s4,s5)  _ftprintf (stdout, (fmt), (s1), (s2), (s3), (s4), (s5))

// 输出错误信息
#define _T_ERROR_PREFIX  _T ("Error: ")  // 错误信息前缀文本
#define PERROR0(s)                   _fputts ((_T_ERROR_PREFIX + CVolString (s) + _T ("\r\n")).GetText (), stderr)
#define PERROR1(fmt,s1)              _fputts ((_T_ERROR_PREFIX + CVolString ().Format ((fmt), (s1)) + _T ("\r\n")).GetText (), stderr)
#define PERROR2(fmt,s1,s2)           _fputts ((_T_ERROR_PREFIX + CVolString ().Format ((fmt), (s1), (s2)) + _T ("\r\n")).GetText (), stderr)
#define PERROR3(fmt,s1,s2,s3)        _fputts ((_T_ERROR_PREFIX + CVolString ().Format ((fmt), (s1), (s2), (s3)) + _T ("\r\n")).GetText (), stderr)
#define PERROR4(fmt,s1,s2,s3,s4)     _fputts ((_T_ERROR_PREFIX + CVolString ().Format ((fmt), (s1), (s2), (s3), (s4)) + _T ("\r\n")).GetText (), stderr)
#define PERROR5(fmt,s1,s2,s3,s4,s5)  _fputts ((_T_ERROR_PREFIX + CVolString ().Format ((fmt), (s1), (s2), (s3), (s4), (s5)) + _T ("\r\n")).GetText (), stderr)

// 输出警告信息
#define _T_WARNING_PREFIX  _T ("Warning: ")  // 警告信息前缀文本
#define PWARNING0(s)                   _fputts ((_T_WARNING_PREFIX + CVolString (s) + _T ("\r\n")).GetText (), stdout)
#define PWARNING1(fmt,s1)              _fputts ((_T_WARNING_PREFIX + CVolString ().Format ((fmt), (s1)) + _T ("\r\n")).GetText (), stdout)
#define PWARNING2(fmt,s1,s2)           _fputts ((_T_WARNING_PREFIX + CVolString ().Format ((fmt), (s1), (s2)) + _T ("\r\n")).GetText (), stdout)
#define PWARNING3(fmt,s1,s2,s3)        _fputts ((_T_WARNING_PREFIX + CVolString ().Format ((fmt), (s1), (s2), (s3)) + _T ("\r\n")).GetText (), stdout)
#define PWARNING4(fmt,s1,s2,s3,s4)     _fputts ((_T_WARNING_PREFIX + CVolString ().Format ((fmt), (s1), (s2), (s3), (s4)) + _T ("\r\n")).GetText (), stdout)
#define PWARNING5(fmt,s1,s2,s3,s4,s5)  _fputts ((_T_WARNING_PREFIX + CVolString ().Format ((fmt), (s1), (s2), (s3), (s4), (s5)) + _T ("\r\n")).GetText (), stdout)

//-----------------------------------------------------------------------------  调试

#ifdef _DEBUG
    #ifndef DEBUG
        #define DEBUG
    #endif
#endif
#ifdef DEBUG
    #ifndef _DEBUG
        #define _DEBUG
    #endif
#endif

#if (defined (__MS_CPP__) && defined (_DEBUG))
    #define _CRTDBG_MAP_ALLOC
    #include <crtdbg.h>
#endif

#undef ASSERT
#undef HASSERT
#undef ASSERT_R_STR
#undef ASSERT_R_STR2
#undef ASSERT_R_STR2_NEG1
#undef ASSERT_R_ADR
#undef ASSERT_RW_ADR
#undef ASSERT_R_DATA
#undef ASSERT_RW_DATA
#undef ASSERT_R_STR_OR_NULL
#undef ASSERT_R_DATA_OR_NULL
#undef ASSERT_RW_DATA_OR_NULL
#undef _R_STR
#undef _R_STR2
#undef _R_STR2_NEG1
#undef _R_ADR
#undef _RW_ADR
#undef _R_DATA
#undef _RW_DATA
#undef COMPILE_TIME_ASSERT
#undef VERIFY
#undef VERIFY_EQUAL
#undef VERIFY_NOT_EQUAL
#undef HVERIFY
#undef FAIL
#undef DEFAULT_FAIL
#undef DEFAULT_ASSERT
#undef ELSE_FAIL
#undef ELSE_ASSERT
#undef TRACE0
#undef TRACE1
#undef TRACE2
#undef TRACE3
#undef TRACE4
#undef TRACE5

#if defined (_DEBUG) && !defined (_VOL_POOL_MEMORY_LEAKS_CHECK_DISABLED)
    // 定义本宏用作在编译调试版时启用内存垃圾检测机制
    #define _VOL_POOL_MEMORY_LEAKS_CHECK_ENABLED
#endif

// 火山视窗程序中输出调试信息时必须使用的前缀文本.
#define _AT_VOL_DEBUG_OUT_STRING_LEADER  "* "
#define _T_VOL_DEBUG_OUT_STRING_LEADER  _T (_AT_VOL_DEBUG_OUT_STRING_LEADER)  // 注意: 此宏必须与视窗项目调试插件中使用的同名宏的值保持一致.

#ifdef _DEBUG
    BOOL_P MAssert (const BOOL_P blpSucceed, const char* szTestCond, const char* szFileName, const INT_P npLineNO);
    BOOL_P VolMsgAssert (const BOOL_P blpSucceed, const char* szTestCond, const char* szFileName, const INT_P npLineNO, const TCHAR* szErrorMessage);

    #ifdef _PF_WINDOWS
        #define DEBUG_PRINT(t)          OutputDebugString (t)
    #else
        #define DEBUG_PRINT(t)          PMSG0 (t)
    #endif
    #define TRACE0(s)                   DEBUG_PRINT ((_T_VOL_DEBUG_OUT_STRING_LEADER + CVolString (s) + _T ("\r\n")).GetText ())
    #define TRACE1(fmt,s1)              DEBUG_PRINT ((_T_VOL_DEBUG_OUT_STRING_LEADER + CVolString ().Format ((fmt), (s1)) + _T ("\r\n")).GetText ())
    #define TRACE2(fmt,s1,s2)           DEBUG_PRINT ((_T_VOL_DEBUG_OUT_STRING_LEADER + CVolString ().Format ((fmt), (s1), (s2)) + _T ("\r\n")).GetText ())
    #define TRACE3(fmt,s1,s2,s3)        DEBUG_PRINT ((_T_VOL_DEBUG_OUT_STRING_LEADER + CVolString ().Format ((fmt), (s1), (s2), (s3)) + _T ("\r\n")).GetText ())
    #define TRACE4(fmt,s1,s2,s3,s4)     DEBUG_PRINT ((_T_VOL_DEBUG_OUT_STRING_LEADER + CVolString ().Format ((fmt), (s1), (s2), (s3), (s4)) + _T ("\r\n")).GetText ())
    #define TRACE5(fmt,s1,s2,s3,s4,s5)  DEBUG_PRINT ((_T_VOL_DEBUG_OUT_STRING_LEADER + CVolString ().Format ((fmt), (s1), (s2), (s3), (s4), (s5)) + _T ("\r\n")).GetText ())
    #define _DEBUG_STATMENT(s)  s
    #define ASSERT(t)                   MAssert ((t), #t, __FILE__, __LINE__)
    #define ASSERT_R_STR(psz)           ASSERT (IsValidString (psz))
    #define ASSERT_R_STR2(psz,num_chars)  ASSERT (IsValidString ((psz), (num_chars)))  // num_chars: 所检查的字符数目,必须大于等于0.
    #define ASSERT_R_STR2_NEG1(psz,num_chars)  ASSERT (IsValidStringSupportLenNeg1 ((psz), (num_chars)))  // num_chars: 所检查的字符数目,必须大于等于-1,为-1表示一直检查到psz文本的零字符处.
    #define ASSERT_R_ADR(p,size)        ASSERT (IsValidAddress ((p), (size), FALSE))
    #define ASSERT_RW_ADR(p,size)       ASSERT (IsValidAddress ((p), (size), TRUE))
    #define ASSERT_R_DATA(pdata)        ASSERT (IsValidDataPointer ((pdata), FALSE))
    #define ASSERT_RW_DATA(pdata)       ASSERT (IsValidDataPointer ((pdata), TRUE))
    #define ASSERT_R_STR_OR_NULL(psz)      ASSERT ((psz) == NULL || IsValidString (psz))
    #define ASSERT_R_DATA_OR_NULL(pdata)   ASSERT ((pdata) == NULL || IsValidDataPointer ((pdata), FALSE))
    #define ASSERT_RW_DATA_OR_NULL(pdata)  ASSERT ((pdata) == NULL || IsValidDataPointer ((pdata), TRUE))
    #define _R_STR(psz)                 (ASSERT (IsValidString (psz)) ? (psz) : NULL)
    #define _R_STR2(psz,num_chars)      (ASSERT (IsValidString ((psz), (num_chars))) ? (psz) : NULL)  // num_chars: 所检查的字符数目,必须大于等于0.
    #define _R_STR2_NEG1(psz,num_chars) (ASSERT (IsValidStringSupportLenNeg1 ((psz), (num_chars))) ? (psz) : NULL)  // num_chars: 所检查的字符数目,必须大于等于-1,为-1表示一直检查到psz文本的零字符处.
    #define _R_ADR(p,size)              (ASSERT (IsValidAddress ((p), (size), FALSE)) ? (p) : NULL)
    #define _RW_ADR(p,size)             (ASSERT (IsValidAddress ((p), (size), TRUE)) ? (p) : NULL)
    #define _R_DATA(pdata)              (ASSERT (IsValidDataPointer ((pdata), FALSE)) ? (pdata) : NULL)
    #define _RW_DATA(pdata)             (ASSERT (IsValidDataPointer ((pdata), TRUE)) ? (pdata) : NULL)
    #ifdef __MS_CPP__
        #define COMPILE_TIME_ASSERT(t)  extern char __dummy [(t) ? 1 : -1]
    #else
        #define COMPILE_TIME_ASSERT(t)  extern char __dummy [(t) ? 1 : -1] __attribute__ ((unused))
    #endif
    #define VERIFY(t)                   ASSERT (t)
    #define VERIFY_EQUAL(t,v)           ASSERT ((t) == (v))
    #define VERIFY_NOT_EQUAL(t,v)       ASSERT ((t) != (v))
    #define FAIL                        ASSERT (FALSE)
    #define DEFAULT_FAIL                default: FAIL; break;
    #define DEFAULT_ASSERT(t)           default: ASSERT (t); break;
    #define ELSE_FAIL                   else FAIL;
    #define ELSE_ASSERT(t)              else ASSERT (t);
    #ifdef _PF_WINDOWS
        #include <winerror.h>
        #define HASSERT(t)              ASSERT (SUCCEEDED (t))
        #define HVERIFY(t)              ASSERT (SUCCEEDED (t))
    #endif
    #define MSG_ASSERT(cond,out_message)  VolMsgAssert ((cond), #cond, __FILE__, __LINE__, out_message)
    #define READ_POINTER_NUMBER(p, num_data_type)  (ASSERT (IsValidAddress ((void*)(p), sizeof (num_data_type), FALSE)) ? *(num_data_type*)(p) : 0)
    #define WRITE_POINTER_NUMBER(p, num_data_type, value)  if (ASSERT (IsValidAddress ((void*)(p), sizeof (num_data_type), TRUE)))  *(num_data_type*)(p) = (num_data_type)(value)
    #define _T_DBG(text)  _T (text)
#else
    #define _DEBUG_STATMENT(s)
    #define DEBUG_PRINT(t)
    #define TRACE0(s)
    #define TRACE1(fmt,s1)
    #define TRACE2(fmt,s1,s2)
    #define TRACE3(fmt,s1,s2,s3)
    #define TRACE4(fmt,s1,s2,s3,s4)
    #define TRACE5(fmt,s1,s2,s3,s4,s5)
    #define ASSERT(t)
    #define ASSERT_R_STR(psz)
    #define ASSERT_R_STR2(psz,num_chars)
    #define ASSERT_R_STR2_NEG1(psz,num_chars)
    #define ASSERT_R_ADR(p,size)
    #define ASSERT_RW_ADR(p,size)
    #define ASSERT_R_DATA(pdata)
    #define ASSERT_RW_DATA(pdata)
    #define ASSERT_R_STR_OR_NULL(psz)
    #define ASSERT_R_DATA_OR_NULL(pdata)
    #define ASSERT_RW_DATA_OR_NULL(pdata)
    #define _R_STR(psz)               psz
    #define _R_STR2(psz,num_chars)    psz
    #define _R_STR2_NEG1(psz,num_chars)  psz
    #define _R_ADR(p,size)            p
    #define _RW_ADR(p,size)           p
    #define _R_DATA(pdata)            pdata
    #define _RW_DATA(pdata)           pdata
    #define COMPILE_TIME_ASSERT(t)
    #define VERIFY(t)                 t
    #define VERIFY_EQUAL(t,v)         t
    #define VERIFY_NOT_EQUAL(t,v)     t
    #ifdef _PF_WINDOWS
        #define HASSERT(t)
        #define HVERIFY(t)            t
    #endif
    #define FAIL
    #define DEFAULT_FAIL
    #define DEFAULT_ASSERT(t)
    #define ELSE_FAIL
    #define ELSE_ASSERT(t)
    #define MSG_ASSERT(cond,out_message)
    #define READ_POINTER_NUMBER(p, num_data_type)  *(num_data_type*)(p)
    #define WRITE_POINTER_NUMBER(p, num_data_type, value)  *(num_data_type*)(p) = (num_data_type)(value)
    #define _T_DBG(text)  _T ("")
#endif

//-----------------------------------------------------------------------------  校验

// 必定满足这些条件
COMPILE_TIME_ASSERT (
        sizeof (INT_P) == sizeof (void*) &&
        sizeof (UINT_P) == sizeof (void*) &&
        sizeof (BOOL_P) == sizeof (void*) &&
        sizeof (INT64) == 8 &&
        sizeof (UINT64) == 8);

// 校验平台位数是否与实际相符
#ifdef _PF_64_BITS
    COMPILE_TIME_ASSERT (sizeof (void*) == 8);  // 64位指针
#else
    COMPILE_TIME_ASSERT (sizeof (void*) == 4);  // 32位指针
#endif

//-----------------------------------------------------------------------------  平台差异

// 定义inline_宏:
/* #if defined (__MS_CPP__)
    #define inline_  __forceinline
#elif defined(__GNUC__) && __GNUC__ < 3
    #define inline_ inline
#elif defined(__GNUC__)
    #define inline_ inline __attribute__ ((always_inline))
#else
    #define inline_ inline
#endif */
#define inline_ inline

#ifdef _PF_LINUX
    #ifndef NULL
        // #define NULL  ((void*)0)
        #define NULL  0
    #endif

    #define override
    #define CALLBACK
    #define PASCAL
#endif

#ifndef PASCAL
    #if (defined (_MSC_VER) && _MSC_VER >= 800) || defined (_STDCALL_SUPPORTED)
        #define CALLBACK  __stdcall
        #define PASCAL  __stdcall
    #else
        #define CALLBACK
        #define PASCAL  pascal
    #endif
#endif

//-----------------------------------------------------------------------------  类运行时信息(注意不支持命名空间)

// 定义类的类型信息(内部宏)
#define _DECLARE_CLASS_TYPE(class_name)  \
    public:                                                                   \
        inline_ static const CQCompareConstU8Text& sGetClassQName ()          \
        {                                                                     \
            static const CQCompareConstU8Text cs_qtClassName (#class_name);   \
            return cs_qtClassName;                                            \
        }                                                                     \
        inline_ static const U8CHAR* sGetClassName ()                         \
        {                                                                     \
            return sGetClassQName ().GetStaticText ();                        \
        }                                                                     \
        virtual const CQCompareConstU8Text& GetClassQName () const            \
        {                                                                     \
            return sGetClassQName ();                                         \
        }                                                                     \
        inline_ const U8CHAR* MGetClassName () const                          \
        {                                                                     \
            return GetClassQName ().GetStaticText ();                         \
        }                                                                     \
        inline_ BOOL_P IsClass (const CQCompareConstU8Text& qtClassName) const  \
        {                                                                     \
            return GetClassQName ().IsEqual (qtClassName);                    \
        }

// 用作支持在单根继承类中通过BaseClass::xxx方式访问其基础类的成员,以及动态类型匹配支持.
// 注意: 一旦使用此机制,则类继承树中的所有类都最好定义此宏.
// DECLARE_BASE_CLASS用作声明最底层的基础类,DECLARE_DERIVED_CLASS用作声明后续的继承类. base_class_name/derived_class_name宏参数为当前类名.
#define DECLARE_BASE_CLASS(base_class_name)  \
    _DECLARE_CLASS_TYPE(base_class_name)                                           \
    public:                                                                        \
        virtual BOOL_P IsInstanceOf (const CQCompareConstU8Text& qtClassName) const  \
        {                                                                          \
            return sGetClassQName ().IsEqual (qtClassName);                        \
        }                                                                          \
    protected:                                                                     \
        typedef base_class_name SelfClass;

#define DECLARE_DERIVED_CLASS(derived_class_name)  \
    _DECLARE_CLASS_TYPE(derived_class_name)                                                 \
    public:                                                                                 \
        typedef SelfClass BaseClass;                                                        \
        virtual BOOL_P IsInstanceOf (const CQCompareConstU8Text& qtClassName) const override  \
        {                                                                                   \
            return (sGetClassQName ().IsEqual (qtClassName) ? TRUE :                        \
                    BaseClass::IsInstanceOf (qtClassName));                                 \
        }                                                                                   \
    protected:                                                                              \
        typedef derived_class_name SelfClass;

// 返回指定对象的类是否为指定名称
#define IS_CLASS(object,class_name)  \
    (object).IsClass (class_name::sGetClassQName ())
#define P_IS_CLASS(pobject,class_name)  \
    ((pobject) != NULL && (pobject)->IsClass (class_name::sGetClassQName ()))

// 返回指定对象或者其基类对象的类是否为指定名称
#define IS_INSTANCE_OF(object,class_name)  \
    (object).IsInstanceOf (class_name::sGetClassQName ())
#define P_IS_INSTANCE_OF(pobject,class_name)  \
    ((pobject) != NULL && (pobject)->IsInstanceOf (class_name::sGetClassQName ()))

// 如果指定对象或者其基类对象的类为指定名称,则将其转换到指定类,否则返回NULL.
#define P_CAST_INSTANCE(pobject,class_name)  \
    (P_IS_INSTANCE_OF (pobject, class_name) ? (class_name*)(pobject) : NULL)

// 相关调试宏
#ifdef _DEBUG
    #define ASSER_IS_CLASS(object,class_name)  ASSERT (IS_CLASS (object, class_name))
    #define ASSER_IS_INSTANCE_OF(object,class_name)  ASSERT (IS_INSTANCE_OF (object, class_name))
    #define ASSER_P_IS_CLASS(pobject,class_name)  ASSERT (P_IS_CLASS (pobject, class_name))
    #define ASSER_P_IS_INSTANCE_OF(pobject,class_name)  ASSERT (P_IS_INSTANCE_OF (pobject, class_name))
    #define ASSER_P_IS_NULL_OR_CLASS(pobject,class_name)  ASSERT ((pobject) == NULL || P_IS_CLASS (pobject, class_name))
    #define ASSER_P_IS_NULL_OR_INSTANCE_OF(pobject,class_name)  ASSERT ((pobject) == NULL || P_IS_INSTANCE_OF (pobject, class_name))
#else
    #define ASSER_IS_CLASS(object,class_name)
    #define ASSER_IS_INSTANCE_OF(object,class_name)
    #define ASSER_P_IS_CLASS(pobject,class_name)
    #define ASSER_P_IS_INSTANCE_OF(pobject,class_name)
    #define ASSER_P_IS_NULL_OR_CLASS(pobject,class_name)
    #define ASSER_P_IS_NULL_OR_INSTANCE_OF(pobject,class_name)
#endif

//-----------------------------------------------------------------------------  内嵌常量字符串表

typedef INT_P CSTR_INX_P;  // 常量字符串表索引值
#define INVALID_CSTR_INDEX  ((CSTR_INX_P)-1)  // 无效的常量字符串表索引值

// 返回指定字符串表的变量名称
#define STRINGS_TABLE_VAR(str_table_name)  COMBINE_MACRO (g_ast_, str_table_name)
// 返回指定字符串表的表项数目
#define NUM_STRINGS_OF_TABLE(str_table_name)  COMBINE_MACRO (_NUM_STRINGS_, str_table_name)

#ifdef _DEBUG
    typedef struct
    {
        CSTR_INX_P m_sip;  // 常量文本索引值
        const TCHAR* m_szStringValue;
        INT_P m_npStringLength;
    }
    STR_TABLE_ITEM;

    // 用作检查字符串表是否定义正确
    class CDebugCheckStringTable
    {
    public:
        CDebugCheckStringTable (const STR_TABLE_ITEM* pStringItem, const INT_P npNumItems)
        {
            // 逐一检查字符串表中所有项目的声明位置与其实现位置是否匹配
            for (INT_P npIndex = 0; npIndex < npNumItems; npIndex++, pStringItem++)
            {
                ASSERT (pStringItem->m_szStringValue != NULL);

                if (pStringItem->m_sip != npIndex)  // 声明位置与其实现位置不匹配?
                {
                    DEBUG_PRINT (_T ("--- The string \""));
                    DEBUG_PRINT (pStringItem->m_szStringValue);
                    DEBUG_PRINT (_T ("\" position check failed.\r\n"));

                    FAIL;
                }
            }
        }
    };

    // 开始定义指定名称的字符串声明表
    //   str_table_name: 常量字符串表的名称
    #define BEGIN_DECLARE_STRINGS_TABLE(str_table_name)  \
        extern const STR_TABLE_ITEM g_ast_##str_table_name [];  \
        enum {

    // 结束定义指定名称的字符串声明表
    #define END_DECLARE_STRINGS_TABLE(str_table_name)  \
        NUM_STRINGS_OF_TABLE (str_table_name)  };

    // 开始定义指定名称的字符串实现表
    #define BEGIN_IMPLEMENT_STRINGS_TABLE(str_table_name)  \
        const STR_TABLE_ITEM g_ast_##str_table_name [] =  \
        {

    // 在字符串实现表中定义所指定名称的字符串
    //   str_ref_name: 字符串引用名称
    //   str_const_value: 对应的字符串常量文本
    #define I_STR(str_ref_name,str_const_value)  \
        {  (INT_P)(str_ref_name), (str_const_value), NUM_CHARS_OF_TEXT (str_const_value)  },

    // 结束定义指定名称的字符串实现表
    #define END_IMPLEMENT_STRINGS_TABLE(str_table_name)  \
        };                                                                                         \
        COMPILE_TIME_ASSERT (NUM_STRINGS_OF_TABLE (str_table_name) ==                              \
                sizeof (g_ast_##str_table_name) / sizeof (g_ast_##str_table_name [0]));            \
        static CDebugCheckStringTable s_str_tab_checker_##str_table_name (g_ast_##str_table_name,  \
                sizeof (g_ast_##str_table_name) / sizeof (g_ast_##str_table_name [0]));

#else

    typedef struct
    {
        const TCHAR* m_szStringValue;
        INT_P m_npStringLength;
    }
    STR_TABLE_ITEM;

    #define BEGIN_DECLARE_STRINGS_TABLE(str_table_name)  \
        extern const STR_TABLE_ITEM g_ast_##str_table_name [];  \
        enum {

    #define END_DECLARE_STRINGS_TABLE(str_table_name)  \
        NUM_STRINGS_OF_TABLE (str_table_name)  };

    #define BEGIN_IMPLEMENT_STRINGS_TABLE(str_table_name)  \
        const STR_TABLE_ITEM g_ast_##str_table_name [] =  \
        {

    #define I_STR(str_ref_name,str_const_value)  \
        {  str_const_value, NUM_CHARS_OF_TEXT (str_const_value)  },

    #define END_IMPLEMENT_STRINGS_TABLE(str_table_name)  \
        };
#endif

// 返回指定名称字符串表中所指定名称的字符串值
#define _S2(str_table_name,str_ref_name)  \
    g_ast_##str_table_name [(INT_P)(str_ref_name)].m_szStringValue

// 返回指定名称字符串表中所指定名称的字符串的长度
#define _SL2(str_table_name,str_ref_name)  \
    g_ast_##str_table_name [(INT_P)(str_ref_name)].m_npStringLength

// 在字符串声明表中声明所指定名称的字符串
#define D_STR(str_ref_name)  str_ref_name,
#define D_STR2(str_ref_name,value)  str_ref_name = (value),

//---------------------------------------

// 定义默认字符串表的声明和实现表
#define _DEFAULT_STRING_TABLE_NAME  def_str_table  // 默认字符串表名称
#define BEGIN_DECLARE_DEFAULT_STRINGS_TABLE    BEGIN_DECLARE_STRINGS_TABLE (_DEFAULT_STRING_TABLE_NAME)
#define END_DECLARE_DEFAULT_STRINGS_TABLE      END_DECLARE_STRINGS_TABLE (_DEFAULT_STRING_TABLE_NAME)
#define BEGIN_IMPLEMENT_DEFAULT_STRINGS_TABLE  BEGIN_IMPLEMENT_STRINGS_TABLE (_DEFAULT_STRING_TABLE_NAME)
#define END_IMPLEMENT_DEFAULT_STRINGS_TABLE    END_IMPLEMENT_STRINGS_TABLE (_DEFAULT_STRING_TABLE_NAME)

// 返回默认字符串表的变量名称
#define DEFAULT_STRINGS_TABLE_VAR  STRINGS_TABLE_VAR (_DEFAULT_STRING_TABLE_NAME)
// 返回默认字符串表的表项数目
#define NUM_STRINGS_OF_DEFAULT_TABLE  NUM_STRINGS_OF_TABLE (_DEFAULT_STRING_TABLE_NAME)

// 用作校验所指定常量字符串所有是否有效
#ifdef _DEBUG
    #define ASSERT_CONST_STR_VALID(sip, str_table_name)  \
            ASSERT ((sip) >= 0 && (sip) < NUM_STRINGS_OF_TABLE (str_table_name))
    #define ASSERT_DT_CONST_STR_VALID(sip)  \
            ASSERT ((sip) >= 0 && (sip) < NUM_STRINGS_OF_DEFAULT_TABLE)
#else
    #define ASSERT_CONST_STR_VALID(sip, str_table_name)
    #define ASSERT_DT_CONST_STR_VALID(sip)
#endif

// 返回默认字符串表中指定文本
#define _S(str_ref_name)  \
    _S2 (_DEFAULT_STRING_TABLE_NAME, str_ref_name)

// 返回默认字符串表中指定文本的长度
#define _SL(str_ref_name)  \
    _SL2 (_DEFAULT_STRING_TABLE_NAME, str_ref_name)

//-----------------------------------------------------------------------------  其它

#ifndef WM_DPICHANGED
#define WM_DPICHANGED  0x02E0
#endif

// 内容的水平对齐方式
typedef enum
{
    VHAM_LEFT = 0,  // 左边对齐
    VHAM_HCENTER,   // 中间对齐
    VHAM_RIGHT      // 右边对齐
}
VOL_HORZ_ALIGN_MODE;

// 内容的垂直对齐方式
typedef enum
{
    VVAM_TOP = 0,  // 顶边对齐
    VVAM_VCENTER,  // 中间对齐
    VVAM_BOTTOM    // 底边对齐
}
VOL_VERT_ALIGN_MODE;

// 浮点数相关
#define NEAR_ZERO_FLOAT   (1e-6f)  // 靠近0的FLOAT
#define NEAR_ZERO_DOUBLE  (1e-6)   // 靠近0的DOUBLE

// 返回是否为十进制数字字符
#define IS_NUMBER_CHAR(ch)  ((UINT_P)(ch) >= (UINT_P)'0' && (UINT_P)(ch) <= (UINT_P)'9')
// 返回是否为十六进制数字字符
#define IS_HEX_NUMBER_CHAR(ch)  (((UINT_P)(ch) >= (UINT_P)'a' && (UINT_P)(ch) <= (UINT_P)'f') || ((UINT_P)(ch) >= (UINT_P)'A' && (UINT_P)(ch) <= (UINT_P)'F') || IS_NUMBER_CHAR (ch))
// 返回指定字符是否为可视字符(可以显示出来的字符)
#define IS_VISIBLE_CHAR(ch) ((UINT_P)(ch) >= (UINT_P)' ')

// 返回指定字符是否为空白字符或者小于空白字符. 注意: 本宏没有处理'\0'字符,调用本宏之前必须将其过滤掉.
// 0x3000为全角空格的Unicode编码值.
#define IS_SPACE_CHAR_NOT_CHECK_ZERO(ch)  ((UINT_P)(ch) <= (UINT_P)' ' || (ch) == 0x3000)
// 返回指定字符是否为可视空白字符
#define IS_VISIBLE_SPACE_CHAR(ch)  ((ch) == ' ' || (ch) == '\t' || (ch) == 0x3000)

// 取最大或最小值
#undef  MIN
#undef  MAX
#define MIN(a, b)    ((a) < (b) ? (a) : (b))  // Returns the min value between a and b
#define MIN3(a,b,c)  ((a) < (b) ? MIN (a,c) : MIN (b,c))  // Returns the min value between a, b and c
#define MAX(a, b)    ((a) > (b) ? (a) : (b))  // Returns the max value between a and b
#define MAX3(a,b,c)  ((a) > (b) ? MAX (a,c) : MAX (b,c))  // Returns the max value between a, b and c

// 返回value值剪切到min_value到max_value之间后的结果
#define CLIP(value,min_value,max_value)  \
    ((value) < (min_value) ? (min_value) : ((value) > (max_value) ? (max_value) : (value)))

// 取最大值函数,用作避免当参数值为函数调用时直接使用宏所导致的重复调用.
template<typename T> inline_ T GetMax (T arg1, T arg2)
{
    return MAX (arg1, arg2);
}
template<typename T> inline_ T GetMax3 (T arg1, T arg2, T arg3)
{
    return MAX3 (arg1, arg2, arg3);
}
// 取最小值函数
template<typename T> inline_ T GetMin (T arg1, T arg2)
{
    return MIN (arg1, arg2);
}
template<typename T> inline_ T GetMin3 (T arg1, T arg2, T arg3)
{
    return MIN3 (arg1, arg2, arg3);
}
// 剪切
template<typename T> inline_ T GetClipValue (T value, T min_value, T max_value)
{
    ASSERT (min_value <= max_value);
    return CLIP (value, min_value, max_value);
}

// 交换数据
#define SWAP(TYPE,a,b)          {  TYPE bak = a;  a = b;  b = bak;  }
#define SWAP_FLOAT(a,b)         SWAP (FLOAT, a, b)
#define SWAP_DOUBLE(a,b)        SWAP (DOUBLE, a, b)
#define SWAP_INT(a,b)           SWAP (INT, a, b)
#define SWAP_INT_P(a,b)         SWAP (INT_P, a, b)
#define SWAP_DWORD(a,b)         SWAP (DWORD, a, b)
#define SWAP_UINT_P(a,b)        SWAP (UINT_P, a, b)
#define SWAP_UINT64(a,b)        SWAP (UINT64, a, b)
#define SWAP_WORD(a,b)          SWAP (WORD, a, b)
#define SWAP_BOOL(a,b)          SWAP (BOOL, a, b)
#define SWAP_BOOL_P(a,b)        SWAP (BOOL_P, a, b)
#define SWAP_VOID_POINTER(a,b)  SWAP (void*, a, b)

// 安全释放
#define MSAFE_RELEASE(pv)       if ((pv) != NULL)  {  (pv)->Release ();  (pv) = NULL;  }
#define MSAFE_DELETE(pv)        if ((pv) != NULL)  {  delete (pv);       (pv) = NULL;  }
#define MSAFE_DELETE_ARRAY(pv)  if ((pv) != NULL)  {  delete[] (pv);     (pv) = NULL;  }

// 内存操作
#ifdef _PF_WINDOWS
    #define ZERO_MEM(p,size)           ::ZeroMemory ((void*)(p), (size_t)(size))
    #define FILL_MEM(p,size,n)         ::FillMemory ((void*)(p), (size_t)(size), (BYTE)(n))
    #define COPY_MEM(pdest,psrc,size)  ::CopyMemory ((void*)(pdest), (void*)(psrc), (size_t)(size))
    #define MOVE_MEM(pdest,psrc,size)  ::MoveMemory ((void*)(pdest), (void*)(psrc), (size_t)(size))
#else
    #define ZERO_MEM(p,size)           ::memset ((void*)(p), 0, (size_t)(size))
    #define FILL_MEM(p,size,n)         ::memset ((void*)(p), (int)(n), (size_t)(size))
    #define COPY_MEM(pdest,psrc,size)  ::memcpy ((void*)(pdest), (void*)(psrc), (size_t)(size))
    #define MOVE_MEM(pdest,psrc,size)  ::memmove ((void*)(pdest), (void*)(psrc), (size_t)(size))
#endif
#define ZERO_ARRAY_VAR(ary_var)  ZERO_MEM (ary_var, sizeof (ary_var))

// 返回是否为大写字母
#define IS_UPPER_CASE(ch)  ((UINT_P)(ch) >= (UINT_P)'A' && (UINT_P)(ch) <= (UINT_P)'Z')
// 返回是否为小写字母
#define IS_LOWER_CASE(ch)  ((UINT_P)(ch) >= (UINT_P)'a' && (UINT_P)(ch) <= (UINT_P)'z')
// 返回是否为字母
#define IS_ALPHA(ch)  (IS_UPPER_CASE (ch) || IS_LOWER_CASE (ch))

// 大小写字母转换
#define TO_UPPER_CASE(ch)  (IS_LOWER_CASE (ch) ? (TCHAR)((UINT_P)(ch) - (UINT_P)'a' + (UINT_P)'A') : (TCHAR)(ch))
#define TO_LOWER_CASE(ch)  (IS_UPPER_CASE (ch) ? (TCHAR)((UINT_P)(ch) - (UINT_P)'A' + (UINT_P)'a') : (TCHAR)(ch))

// 转换到大写字母
inline_ TCHAR ToUpperCase (const TCHAR ch)
{
    const UINT_P upChar = ch;
    return TO_UPPER_CASE (upChar);
}

// 转换到小写字母
inline_ TCHAR ToLowerCase (const TCHAR ch)
{
    const UINT_P upChar = ch;
    return TO_LOWER_CASE (upChar);
}

// WORD操作
#undef MAKE_WORD
#undef LOW_BYTE
#undef HIGH_BYTE
#undef LOW_CHAR
#undef HIGH_CHAR
#define MAKE_WORD(lobyte, hibyte)  ((WORD)(((BYTE)(((UINT_P)(lobyte)) & 0xFF)) | ((WORD)((BYTE)(((UINT_P)(hibyte)) & 0xFF))) << 8))
#define LOW_BYTE(w)   ((UINT_P)(w) & 0xFF)
#define HIGH_BYTE(w)  (((UINT_P)(w) >> 8) & 0xFF)
#define LOW_CHAR(w)   (INT_P)(char)LOW_BYTE (w)
#define HIGH_CHAR(w)  (INT_P)(char)HIGH_BYTE (w)

// DWORD操作
#undef MAKE_DWORD
#undef LOW_WORD
#undef HIGH_WORD
#undef LOW_SHORT
#undef HIGH_SHORT
#define MAKE_DWORD(loword, hiword)  (((DWORD)(loword) & 0xFFFF) | (((DWORD)(hiword) & 0xFFFF) << 16))
#define LOW_WORD(dw)    ((UINT_P)(dw) & 0xFFFF)
#define HIGH_WORD(dw)   (UINT_P)((DWORD)(dw) >> 16)
#define LOW_SHORT(dw)   (INT_P)(SHORT)LOW_WORD (dw)
#define HIGH_SHORT(dw)  (INT_P)(SHORT)HIGH_WORD (dw)

// QWORD操作
#define QW_MAKE_QWORD(lodword, hidword)  (((UINT64)(DWORD)(lodword)) | (((UINT64)(DWORD)(hidword)) << 32))
#define QW_LOW_DWORD(qw)   (UINT_P)(DWORD)(qw)
#define QW_HIGH_DWORD(qw)  (UINT_P)((UINT64)(qw) >> 32)
#define QW_LOW_INT(qw)     (INT_P)(INT)QW_LOW_DWORD (qw)
#define QW_HIGH_INT(qw)    (INT_P)(INT)QW_HIGH_DWORD (qw)

// 反转字节顺序
#define REVERSE_WORD(w)  ((((w) & 0x00FF) << 8) | (((w) & 0xFF00) >> 8))
#define REVERSE_DWORD(dw)  ((REVERSE_WORD ((dw) & 0xFFFF) << 16) | REVERSE_WORD (((dw) >> 16) & 0xFFFF))

// 返回数组的成员数目(注意不适用多维数组)
#define NUM_ELEMENTS_OF(ary)  ((INT_P)(sizeof (ary) / sizeof ((ary) [0])))
#define NUM_ELEMENTS_OF2(s,m)  NUM_ELEMENTS_OF (((s*)0)->m)
#define _ARRAY_NAME_AND_ELEMENT_COUNT(ary)  (ary), NUM_ELEMENTS_OF (ary)

#define SIZE_ELEMENT_OF(s,m)  (sizeof (((s*)0)->m))  // 返回s数据类型的m成员的尺寸
#define OFFSET_ELEMENT_OF(s,m)  (INT_P)&(((s*)0)->m)  // 返回返回s数据类型的m成员在s中的偏移

// 返回文本常量的字符数目(不包括结束'\0'字符)
#define NUM_CHARS_OF_TEXT(text)  (NUM_ELEMENTS_OF (text) - 1)
COMPILE_TIME_ASSERT (NUM_CHARS_OF_TEXT ("code") == 4 && NUM_CHARS_OF_TEXT (L"code") == 4);

// 将NULL文本指针转换为空文本指针
#define _TN2E(ps)  ((ps) == NULL ? _T ("") : (ps))

// 用作定义文本及其相关信息
#define _T_WITH_LEN(text)    _T (text), NUM_CHARS_OF_TEXT (_T (text))
#define _T_WITH_HASH(text)   _T (text), ::GetTextHash (_T (text))
#define _T_WITH_IHASH(text)  _T (text), ::GetTextIHash (_T (text))

// 文件路径分隔符
#ifdef _PF_WINDOWS
    #define OS_PATH_CHAR       '\\'
    #define OS_PATH_CHAR_TEXT  _T ("\\")
#else
    #define OS_PATH_CHAR       '/'
    #define OS_PATH_CHAR_TEXT  _T ("/")
#endif

// 最大文件路径名长度
#ifndef _PF_WINDOWS
    #define MAX_PATH  PATH_MAX
#endif

// 十六进制数值的引导文本
#define HEX_NUM_LEADER_TEXT  _T ("0x")
#define HEX_NUM_LEADER_TEXT_A  "0x"
#define HEX_NUM_LEADER_TEXT_W  L"0x"

// 调色板索引颜色的建立与解析
#define MAKE_PAL_COLOR(clr_index)  ((COLORREF)(0x01000000 | (DWORD)(WORD)(clr_index)))  // 建立调色板颜色
#define IS_PAL_COLOR(clr)  (((clr) & 0xFF000000) == 0x01000000)  // 返回指定颜色值是否为调色板颜色
#define GET_PAL_COLOR_INDEX(pal_clr)  (INT_P)((DWORD)(pal_clr) & 0xFFFF)  // 返回调色板颜色所对应的索引值
// 一些特定颜色:
#define _CLR_DEFAULT  ((COLORREF)-1)  // 默认颜色(最好不更改此值,该值需要与MFC库中的代码保持一致)
#define _CLR_TRANSPARENT  ((COLORREF)-2)  // 透明颜色

// 角度
#undef PI
#define PI  3.1415926535897932384626433832795028841971693993751f
#define TO_RADIAN(degree)  ((FLOAT)((degree) * (PI / 180.0f)))
#define TO_DEGREE(radian)  ((FLOAT)((radian) * (180.0f / PI)))

#define NUM_USECS_OF_SECOND  1000000  // 每秒中的微秒数

#define DWORD_SIGN_BIT  ((DWORD)(1 << 31))  // 仅最高符号位被置为1的DWORD数据
#define DWORD_BITS_WITHOUT_SIGN  (~DWORD_SIGN_BIT)  // 仅最高符号位未被置为1的DWORD数据

// 通用无效ID值
#define _INVALID_ID  ((UINT_P)-1)

// 缩进空白文本
#define NUM_INDENT_SPACES  4  // 单个缩进层次所对应的空格数目
#define _T_INDENT_SPACES  _T ("    ")  // 单个缩进层次所对应的空格文本
#define _T_INDENT_SPACES_2  _T_INDENT_SPACES _T_INDENT_SPACES
#define _T_INDENT_SPACES_3  _T_INDENT_SPACES_2 _T_INDENT_SPACES
#define _T_INDENT_SPACES_4  _T_INDENT_SPACES_3 _T_INDENT_SPACES
#define _T_INDENT_SPACES_5  _T_INDENT_SPACES_4 _T_INDENT_SPACES

// 只有这样编译器才会正常链接宏参数名称文本...
#define COMBINE_MACRO(a, b)  _COMBINE_MACRO_(a, b)
#define _COMBINE_MACRO_(a, b)  a##b

// 调用构造函数
//   class_name: 类名
//   p_object: 已有的class_name对象内存指针
//   arg: 构造参数
#define CALL_CONSTRUCTOR0(class_name, p_object)  (new (p_object) class_name)
#define CALL_CONSTRUCTOR1(class_name, p_object, arg1)  (new (p_object) class_name (arg1))
#define CALL_CONSTRUCTOR2(class_name, p_object, arg1, arg2)  (new (p_object) class_name (arg1, arg2))
#define CALL_CONSTRUCTOR3(class_name, p_object, arg1, arg2, arg3)  (new (p_object) class_name (arg1, arg2, arg3))
#define CALL_CONSTRUCTOR4(class_name, p_object, arg1, arg2, arg3, arg4)  (new (p_object) class_name (arg1, arg2, arg3, arg4))
#define CALL_CONSTRUCTOR5(class_name, p_object, arg1, arg2, arg3, arg4, arg5)  (new (p_object) class_name (arg1, arg2, arg3, arg4, arg5))

// 逻辑值英文立即数文本
#define _T_V_EN_TRUE  _T ("true")
#define _T_V_EN_FALSE  _T ("false")
// 返回所指定文本是否为对应逻辑值英文立即数文本
#define IS_EN_TRUE_TEXT(text)  (_tcscmp ((text), _T_V_EN_TRUE) == 0)
#define IS_EN_FALSE_TEXT(text)  (_tcscmp ((text), _T_V_EN_FALSE) == 0)
// 返回所指定文本是否为有效逻辑值英文立即数文本
#define IS_VALID_EN_BOOL_VALUE_TEXT(text)  (IS_EN_TRUE_TEXT (text) || IS_EN_FALSE_TEXT (text))
// 返回对应逻辑值的英文立即数文本
#define GET_EN_BOOL_TEXT(bl)  ((bl) ? _T_V_EN_TRUE : _T_V_EN_FALSE)

// 空对象英文立即数文本(由于本值会用作与java进行交互,所以必须注意与java的String.valueOf的返回值一致)
#define _T_V_EN_NULL  _T ("null")
// 返回所指定文本是否为空对象英文立即数文本
#define IS_EN_NULL_TEXT(text)  (_tcscmp ((text), _T_V_EN_NULL) == 0)

// Socket句柄类型
#ifdef _PF_WINDOWS
    typedef SOCKET HMSOCKET;
    COMPILE_TIME_ASSERT (SOCKET_ERROR == -1);  // 错误值必须为-1,以确保和linux下的一致.
#else
    typedef int HMSOCKET;
#endif

// 无效的socket句柄值
#if defined (_PF_WINDOWS)
    #define _INVALID_MSOCKET_HANDLE  INVALID_SOCKET
    COMPILE_TIME_ASSERT (INVALID_SOCKET == -1);  // 必须为-1,以确保和linux下的一致.
#else
    #define _INVALID_MSOCKET_HANDLE  (-1)
#endif

// 定义一个用作赋予NULL值的参考对象
#define _VOL_NULL_REF_OBJECT(class_name)  (*(class_name*)NULL)

// 返回所指定变量的地址和尺寸
#define _VOL_GET_VAR_ADR_AND_SIZE(var)  (void*)&var, (INT_P)sizeof (var)
// 返回所指定数组变量的地址和尺寸
#define _VOL_GET_ARY_VAR_ADR_AND_SIZE(var)  (void*)var, (INT_P)sizeof (var)

// 类型转换函数
template<class TConvertFrom, class TConvertTo> void* TVolConvertClass (void* pobjFrom)
{
    return (TConvertTo*)(TConvertFrom*)pobjFrom;
}
typedef void* (*FN_VOL_CONVERT_CLASS) (void* pobjFrom);

//-----------------------------------------------------------------------------  原子操作

// 原子性将一个INT变量值加1
#if defined (_PF_WIN32)
    #define INC_INT32_VAR_A(nVarName)  _asm lock inc nVarName
#elif defined (_PF_WIN64)
    #define INC_INT32_VAR_A(nVarName)  _InterlockedIncrement ((LONG*)&nVarName);
#elif defined (_PF_LINUX)
    #define INC_INT32_VAR_A(nVarName)  __asm__ __volatile__ ("lock incl %0": "=m"(nVarName));
#else
    #error Not be supported.
#endif

// 原子性将一个INT变量值减1
#if defined (_PF_WIN32)
    #define DEC_INT32_VAR_A(nVarName)  _asm lock dec nVarName
#elif defined (_PF_WIN64)
    #define DEC_INT32_VAR_A(nVarName)  _InterlockedDecrement ((LONG*)&nVarName);
#elif defined (_PF_LINUX)
    #define DEC_INT32_VAR_A(nVarName)  __asm__ __volatile__ ("lock decl %0": "=m"(nVarName));
#else
    #error Not be supported.
#endif

// 原子性将一个INT64变量值加1
#if defined (_PF_WIN64)
    #define INC_INT64_VAR_A(n64VarName)  _InterlockedIncrement64 ((LONGLONG*)&n64VarName);
#elif defined (_PF_LINUX64)
    #define INC_INT64_VAR_A(n64VarName)  __asm__ __volatile__ ("lock incq %0": "=m"(n64VarName));
#endif

// 原子性将一个INT64变量值减1
#if defined (_PF_WIN64)
    #define DEC_INT64_VAR_A(n64VarName)  _InterlockedDecrement64 ((LONGLONG*)&n64VarName);
#elif defined (_PF_LINUX64)
    #define DEC_INT64_VAR_A(n64VarName)  __asm__ __volatile__ ("lock decq %0": "=m"(n64VarName));
#endif

// 原子性将一个INT_P变量值加1
#if defined (_PF_32_BITS)
    #define INC_INTP_VAR_A(npVarName)  INC_INT32_VAR_A(npVarName)
#elif defined (_PF_64_BITS)
    #define INC_INTP_VAR_A(npVarName)  INC_INT64_VAR_A(npVarName)
#else
    #error Not be supported.
#endif

// 原子性将一个INT_P变量值减1
#if defined (_PF_32_BITS)
    #define DEC_INTP_VAR_A(npVarName)  DEC_INT32_VAR_A(npVarName)
#elif defined (_PF_64_BITS)
    #define DEC_INTP_VAR_A(npVarName)  DEC_INT64_VAR_A(npVarName)
#else
    #error Not be supported.
#endif

//----------------------------------------  类成员操作

#if defined (_PF_WIN32)
    #define INC_INT32_MEMBER_A_WIN32(nMemberName)  \
            _asm mov eax, [this]  \
            _asm lock inc dword ptr [eax + nMemberName]
    #define DEC_INT32_MEMBER_A_WIN32(nMemberName)  \
            _asm mov eax, [this]  \
            _asm lock dec dword ptr [eax + nMemberName]
#endif

// 原子性将一个类的INT成员变量加1
#if defined (_PF_WIN32)
    #define INC_INT32_MEMBER_A(nMemberName)  INC_INT32_MEMBER_A_WIN32(nMemberName)
#else
    #define INC_INT32_MEMBER_A(nMemberName)  INC_INT32_VAR_A(nMemberName)
#endif

// 原子性将一个类的INT成员变量减1
#if defined (_PF_WIN32)
    #define DEC_INT32_MEMBER_A(nMemberName)  DEC_INT32_MEMBER_A_WIN32(nMemberName)
#else
    #define DEC_INT32_MEMBER_A(nMemberName)  DEC_INT32_VAR_A(nMemberName)
#endif

// 原子性将一个类的INT64成员变量加1
#if (defined (_PF_64_BITS))
    #define INC_INT64_MEMBER_A(n64MemberName)  INC_INT64_VAR_A(n64MemberName)
#endif

// 原子性将一个类的INT64成员变量减1
#if (defined (_PF_64_BITS))
    #define DEC_INT64_MEMBER_A(n64MemberName)  DEC_INT64_VAR_A(n64MemberName)
#endif

// 原子性将一个类的INT_P成员变量加1
#if defined (_PF_WIN32)
    #define INC_INTP_MEMBER_A(npMemberName)  INC_INT32_MEMBER_A_WIN32(npMemberName)
#else
    #define INC_INTP_MEMBER_A(npMemberName)  INC_INTP_VAR_A(npMemberName)
#endif

// 原子性将一个类的INT_P成员变量减1
#if defined (_PF_WIN32)
    #define DEC_INTP_MEMBER_A(npMemberName)  DEC_INT32_MEMBER_A_WIN32(npMemberName)
#else
    #define DEC_INTP_MEMBER_A(npMemberName)  DEC_INTP_VAR_A(npMemberName)
#endif

//-----------------------------------------------------------------------------

// "pm_types"中的各种数据类型标识字符文本
#define _T_PMT_VOL_SBYTE                  _T ("b")  // 字节
#define _T_PMT_VOL_SHORT                  _T ("s")  // 短整数
#define _T_PMT_VOL_WCHAR                  _T ("c")  // 字符
#define _T_PMT_VOL_INT                    _T ("n")  // 整数
#define _T_PMT_VOL_VINT                   _T ("p")  // 变整数
#define _T_PMT_VOL_LONG                   _T ("l")  // 长整数
#define _T_PMT_VOL_FLOAT                  _T ("F")  // 单精度小数
#define _T_PMT_VOL_DOUBLE                 _T ("f")  // 小数
#define _T_PMT_VOL_BOOL                   _T ("B")  // 逻辑型
#define _T_PMT_VOL_STRING                 _T ("S")  // 文本型
#define _T_PMT_VOL_CLASS                  _T ("C")  // 火山类
#define _T_PMT_VOL_METHOD                 _T ("M")  // 方法
#define _T_PMT_NATIVE_CLASS               _T ("w")  // 本地类
#define _T_PMT_NATIVE_STRUCT              _T ("W")  // 本地结构
#define _T_PMT_NATIVE_NUM_BASE_DATA_TYPE  _T ("N")  // 本地整数基本类型
#define _T_PMT_NATIVE_VALUE_DATA_TYPE     _T ("v")  // 本地值类型
#define _T_PMT_NATIVE_REF_DATA_TYPE       _T ("r")  // 本地参考类型
// "pm_types"中的各种数据类型标识字符
#define _C_VOL_SBYTE                      'b'  // 字节
#define _C_VOL_SHORT                      's'  // 短整数
#define _C_VOL_WCHAR                      'c'  // 字符
#define _C_VOL_INT                        'n'  // 整数
#define _C_VOL_VINT                       'p'  // 变整数
#define _C_VOL_LONG                       'l'  // 长整数
#define _C_VOL_FLOAT                      'F'  // 单精度小数
#define _C_VOL_DOUBLE                     'f'  // 小数
#define _C_VOL_BOOL                       'B'  // 逻辑型
#define _C_VOL_STRING                     'S'  // 文本型
#define _C_VOL_CLASS                      'C'  // 火山类
#define _C_VOL_METHOD                     'M'  // 方法
#define _C_NATIVE_CLASS                   'w'  // 本地类
#define _C_NATIVE_STRUCT                  'W'  // 本地结构
#define _C_NATIVE_NUM_BASE_DATA_TYPE      'N'  // 本地整数基本类型
#define _C_NATIVE_VALUE_DATA_TYPE         'v'  // 本地值类型
#define _C_NATIVE_REF_DATA_TYPE           'r'  // 本地参考类型

#endif
