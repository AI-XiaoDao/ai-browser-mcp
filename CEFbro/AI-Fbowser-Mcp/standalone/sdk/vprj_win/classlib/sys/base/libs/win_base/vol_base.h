
#ifndef __VOL_BASE_H__
#define __VOL_BASE_H__

// 凡是使用本宏括住的单个名称或者标注有本宏名称注释的代码块中的所有名称,均在编译器中被约定使用,不可被更改.
#define _NAME_COMPILER_AGREED(name)  name

// _NAME_COMPILER_AGREED
#if (defined (_UNICODE) || defined (UNICODE))
    #define CVolString CWString
    #define CVolConstString CWConstString
    #define CMStringWithHash CWStringWithHash
    #define CMStringWithIHash CWStringWithIHash
    #define CMBufString CWBufString
    #define CQCompareConstText CQCompareConstWText
    #define CQCompareIConstText CQCompareIConstWText
#else
    #define CVolString CU8String
    #define CVolConstString CU8ConstString
    #define CMStringWithHash CU8StringWithHash
    #define CMStringWithIHash CU8StringWithIHash
    #define CMBufString CU8BufString
    #define CQCompareConstText CQCompareConstU8Text
    #define CQCompareIConstText CQCompareIConstU8Text
#endif

//------------------------------------------------------------------------------------

#include "include/vol_decl.h"
#include "include/vol_public.h"
#include "include/tr_vol_const.h"
#include "include/vol_functions.h"
#include "include/vol_time.h"
#include "include/vol_string_func.h"
#include "include/vol_mem_pool.h"
#include "include/vol_object.h"
#include "include/vol_mem.h"
#include "include/vol_string_class.h"
#include "include/vol_stream.h"
#include "include/vol_math.h"
#include "include/vol_key.h"
#include "include/vol_array.h"
#include "include/vol_muti_thread.h"
#include "include/vol_sort_array.h"
#include "include/vol_string_array.h"
#include "include/vol_unique_array.h"
#include "include/vol_classes.h"
#include "include/vol_bitmap.h"
#include "include/vol_app_instance.h"
#include "include/vol_com.h"
#include "include/vol_network.h"
#include "include/vol_menu.h"

#endif
