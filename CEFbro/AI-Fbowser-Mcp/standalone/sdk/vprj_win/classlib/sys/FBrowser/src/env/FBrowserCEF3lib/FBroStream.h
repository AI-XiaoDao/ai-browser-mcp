#pragma once
#ifndef FBROWSER_STREAM_H_
#define FBROWSER_STREAM_H_


#ifndef _FBROELIB

DLLEXPORT CefRefPtr<CefStreamReader> TEXPORTS FBroStream_CreateForFile(const CefString& fileName);
DLLEXPORT CefRefPtr<CefStreamReader> TEXPORTS FBroStream_CreateForData(void* data, size_t size);


DLLEXPORT size_t TEXPORTS FBroStream_Read(CefRefPtr<CefStreamReader> streamreader, void* ptr, size_t size, size_t n);
DLLEXPORT int TEXPORTS FBroStream_Seek(CefRefPtr<CefStreamReader> streamreader, int64_t offset, int whence);
DLLEXPORT int64_t TEXPORTS FBroStream_Tell(CefRefPtr<CefStreamReader> streamreader);
DLLEXPORT int TEXPORTS FBroStream_Eof(CefRefPtr<CefStreamReader> streamreader);
DLLEXPORT  bool TEXPORTS FBroStream_MayBlock(CefRefPtr<CefStreamReader> streamreader);

#endif // !_FBROELIB





//handler模式暂不使用
//class FBroReadHandler : public CefReadHandler {
//public:
//	FBroReadHandler() {};
//	~FBroReadHandler() {};
//
//	// Read raw binary data.
//	virtual size_t Read(void* ptr, size_t size, size_t n) override { return 0; };
//
//	// Seek to the specified offset position. |whence| may be any one of
//	// SEEK_CUR, SEEK_END or SEEK_SET. Return zero on success and non-zero on
//	// failure.
//	virtual int Seek(int64_t offset, int whence) override { return 0; };
//
//	// Return the current offset position.
//	virtual int64_t Tell() override { return 0; }
//
//	// Return non-zero if at end of file.
//	virtual int Eof() override { return 0; };
//
//	// Return true if this handler performs work like accessing the file system
//	// which may block. Used as a hint for determining the thread to access the
//	// handler from.
//	virtual bool MayBlock() override { return false; };
//	
//
//protected:
//	IMPLEMENT_REFCOUNTING(FBroReadHandler);
//};

#endif