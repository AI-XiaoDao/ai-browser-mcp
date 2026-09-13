
// Copyright (C) Recursion Company. All rights reserved.

#ifndef __VOL_STRING_CLASS_H__
#define __VOL_STRING_CLASS_H__

// 火山文本编码类型
typedef enum
{
    VSET_UNKNOWN = -1,
    VSET_UTF_16,
    VSET_UTF_8,
    VSET_MBCS  // 多字节本地字符编码
}
VOL_STRING_ENCODE_TYPE;

#define _MY_WSTRING_IMPL
#include "_vol_str_class_impl.h"

#undef _MY_WSTRING_IMPL
#include "_vol_str_class_impl.h"

// 火山常量文本. _NAME_COMPILER_AGREED
#define _CT(x)  CVolConstString (_T (x))
#define _CT2(x)  CVolConstString (x)

#endif
