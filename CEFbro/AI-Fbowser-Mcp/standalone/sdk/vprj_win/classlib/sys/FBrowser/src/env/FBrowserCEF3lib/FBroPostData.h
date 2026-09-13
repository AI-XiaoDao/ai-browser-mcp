#pragma once
#ifndef FBROWSER_POSTDATA_H_
#define FBROWSER_POSTDATA_H_

class FBroPostDataList;
class FBroString;

#ifndef _FBROELIB

DLLEXPORT CefRefPtr<FBroPostDataList> TEXPORTS FBroHsPostData_GetElements(CefRefPtr<CefPostData> PostData);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsPostDataElement_GetFile(CefRefPtr<CefPostDataElement> PostDataElement);
DLLEXPORT CefRefPtr<CefPostData>  TEXPORTS FBroHsPostData_Create();
DLLEXPORT BOOL TEXPORTS FBroHsPostData_IsReadOnly(CefRefPtr<CefPostData> PostData);
DLLEXPORT BOOL TEXPORTS FBroHsPostData_HasExcludedElements(CefRefPtr<CefPostData> PostData);
DLLEXPORT int TEXPORTS FBroHsPostData_GetElementCount(CefRefPtr<CefPostData> PostData);
DLLEXPORT void TEXPORTS FBroHsPostData_RemoveElement(CefRefPtr<CefPostData> PostData, CefRefPtr<CefPostDataElement> element);
DLLEXPORT void TEXPORTS FBroHsPostData_AddElement(CefRefPtr<CefPostData> PostData, CefRefPtr<CefPostDataElement> element);
DLLEXPORT void TEXPORTS FBroHsPostData_RemoveElements(CefRefPtr<CefPostData> PostData);
DLLEXPORT CefRefPtr<CefPostDataElement> TEXPORTS FBroHsPostDataElement_Create();
DLLEXPORT BOOL TEXPORTS FBroHsPostDataElement_IsReadOnly(CefRefPtr<CefPostDataElement> PostDataElement);
DLLEXPORT void TEXPORTS FBroHsPostDataElement_SetToEmpty(CefRefPtr<CefPostDataElement> PostDataElement);
DLLEXPORT void TEXPORTS FBroHsPostDataElement_SetToFile(CefRefPtr<CefPostDataElement> PostDataElement, const CefString& infilename);
DLLEXPORT void TEXPORTS FBroHsPostDataElement_SetToData(CefRefPtr<CefPostDataElement> PostDataElement, void* data, size_t size);
DLLEXPORT void TEXPORTS FBroHsPostDataElement_SetToBytes(CefRefPtr<CefPostDataElement> PostDataElement, const CefString& bytes);
DLLEXPORT int TEXPORTS FBroHsPostDataElement_GetType(CefRefPtr<CefPostDataElement> PostDataElement);
DLLEXPORT int TEXPORTS FBroHsPostDataElement_GetBytesCount(CefRefPtr<CefPostDataElement> PostDataElement);
DLLEXPORT void TEXPORTS FBroHsPostDataElement_GetBytes(CefRefPtr<CefPostDataElement> PostDataElement, size_t size, void* bytes);

#endif // !_FBROELIB




#endif