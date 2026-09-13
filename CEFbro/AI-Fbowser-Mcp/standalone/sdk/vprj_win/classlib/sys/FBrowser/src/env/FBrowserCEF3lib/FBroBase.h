#pragma once

#ifndef FBRO_BASE_H
#define FBRO_BASE_H

#define _CRT_SECURE_NO_WARNINGS

//using namespace std;

#define TEXPORTS __stdcall


#define DLLEXPORT __declspec(dllexport)

#define INTLIST  std::vector<int64_t>
#define CEFSTRINGLIST std::vector<CefString>

#define ISNULL(x) !x
#define ISNULL_REFPTR(x) ISNULL(x) || !x.get()
#define ISNULL_REFPTR_RT(x) if(ISNULL_REFPTR(x)) return
#define ISNULL_REFPTR_RT_RETURN(x,r) if(ISNULL_REFPTR(x)) return r
#define ISBAD_PTR(x,s)  IsBadCodePtr((FARPROC)x) || IsBadReadPtr((void *)x,s)
#define ISBAD_PTR_RT(x,s) if(ISBAD_PTR(x,s)) return //指针错误直接返回
#define ISBAD_PTR_RT_RETURN(x,s,r) if(ISBAD_PTR(x,s)) return r


//#pragma comment(lib,"User32.lib")


//易取空白文本
typedef char* (*SetNullText)(int);

#endif