#pragma once
#ifndef FBROWSER_GLOBALINTERFACE_H_
#define FBROWSER_GLOBALINTERFACE_H_

//这个头文件主要为了方便不同dll直接调用接口函数
class FBroResourceHandler;
class FBroHsResourceHandler;

DLLEXPORT CefRefPtr<FBroResourceHandler> TEXPORTS FBroHsResourceHandler_Create(CefRefPtr<FBroHsResourceHandler> hsrequesthandler);


#endif