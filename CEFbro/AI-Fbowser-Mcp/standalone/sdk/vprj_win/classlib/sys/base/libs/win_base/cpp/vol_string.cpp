
// Copyright (C) Recursion Company. All rights reserved.

#include "../vol_base.h"

#ifdef _DEBUG
    #define MCHECK_STR_POINTER(p)  \
        if ((BYTE*)(p) >= m_mem.GetPtr () && (BYTE*)(p) < m_mem.GetPtr () + m_mem.GetSize ())  \
            ASSERT (FALSE);
#else
    #define MCHECK_STR_POINTER(p)
#endif

//---------------------------------------------------------------------

#define _MY_WSTRING_IMPL
#include "_vol_str_impl.cpp"

#undef _MY_WSTRING_IMPL
#include "_vol_str_impl.cpp"
