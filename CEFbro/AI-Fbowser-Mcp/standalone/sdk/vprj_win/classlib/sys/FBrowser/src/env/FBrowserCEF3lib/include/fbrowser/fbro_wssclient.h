#ifndef CEF_INCLUDE_FBRO_WSSCLIENT_H_
#define CEF_INCLUDE_FBRO_WSSCLIENT_H_

// 可能是在E:\cef107.0.5304.88\source\chromium\src\cef\cef_paths.gypi中声明

#include "include/cef_base.h"

// V8环境内的wss客户端
class FBroDOMWssClient : public virtual CefBaseRefCounted {
 public:
  static CefRefPtr<FBroDOMWssClient> Create(HANDLE wssPtr);

  virtual void SetWssPtr(HANDLE wssPtr) = 0;

  virtual void SetIsClose() = 0;

  // 是否为空
  virtual bool IsNull() = 0;

  // 是否相同
  virtual bool IsSame(CefRefPtr<FBroDOMWssClient> that) = 0;

  // 连接wss服务器
  virtual void Connect(const CefString& url, const CefString& protocol) = 0;
  // 关闭连接
  virtual void Close() = 0;
  // 销毁连接
  virtual void Destroy() = 0;
  // 发送文本
  virtual void Send(const CefString&) = 0;
  // 发送数据
  virtual void SendData(void*, size_t) = 0;
  // 取连接地址
  virtual CefString GetAddress() = 0;
  // 取连接端口
  virtual CefString GetProtocol() = 0;
  virtual CefString GetExtensions() = 0;
  virtual CefString GetBinaryType() = 0;
};

#endif
