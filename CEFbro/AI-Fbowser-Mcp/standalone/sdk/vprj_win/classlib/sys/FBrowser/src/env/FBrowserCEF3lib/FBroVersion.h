#pragma once

#define VERSIONS_MAIN 5
#define VERSIONS_EDIT 36
#define VERSIONS_DEBUG 4101

// 定义一个辅助宏，用于将数字转换为字符串
#define STR_HELPER(x) #x
#define STR(x) STR_HELPER(x)

#define VERSIONS STR(VERSIONS_MAIN) "." STR(VERSIONS_EDIT) "." STR(VERSIONS_DEBUG)

DLLEXPORT int TEXPORTS FBroHsVersion_GetMain();
DLLEXPORT int TEXPORTS FBroHsVersion_GetEdit();
DLLEXPORT int TEXPORTS FBroHsVersion_GetDedug();