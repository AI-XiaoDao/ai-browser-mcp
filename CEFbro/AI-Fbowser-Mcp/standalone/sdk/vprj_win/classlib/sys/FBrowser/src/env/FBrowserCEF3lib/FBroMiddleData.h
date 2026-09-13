#pragma once
#ifndef FBROWSER_MIDDLEDATA_H_
#define FBROWSER_MIDDLEDATA_H_

#include "pch.h"
#include "FBroBrowser.h"

class FBroString;


class FBroDoubleString : public virtual CefBaseRefCounted
{
public:
	virtual int Size() = 0;
	virtual void ToBegin() = 0;
	virtual void ToEnd() = 0;
	virtual bool ToNext() = 0;
	virtual void Add(const CefString& key, const CefString& value) = 0;
	virtual bool Delete(const CefString& key) = 0;
	virtual void Clear() = 0;
	virtual void SetCurrentData(const CefString& value) = 0;
	virtual CefString FindKeyValue(const CefString& key) = 0;
	virtual CefString GetCurrentData_Key() = 0;
	virtual CefString GetCurrentData_Value() = 0;
	virtual std::multimap<CefString, CefString>& GetData() = 0;
};

DLLEXPORT CefRefPtr<FBroDoubleString> FBroDoubleString_Creat(const std::map<CefString, CefString>& data);
DLLEXPORT CefRefPtr<FBroDoubleString> FBroDoubleString_Creat(const std::multimap<CefString, CefString>& data);
DLLEXPORT CefRefPtr<FBroDoubleString> FBroDoubleString_Creat();

//内部动态调用
DLLEXPORT std::multimap<CefString, CefString>& FBroDoubleString_GetData(CefRefPtr<FBroDoubleString> data);

DLLEXPORT void FBroDoubleString_ToBegin(CefRefPtr<FBroDoubleString> data);
DLLEXPORT void FBroDoubleString_ToEnd(CefRefPtr<FBroDoubleString> data);
DLLEXPORT BOOL FBroDoubleString_ToNext(CefRefPtr<FBroDoubleString> data);
DLLEXPORT CefRefPtr<FBroString> FBroDoubleString_GetCurrentData_Key(CefRefPtr<FBroDoubleString> data);
DLLEXPORT CefRefPtr<FBroString> FBroDoubleString_GetCurrentData_Value(CefRefPtr<FBroDoubleString> data);
DLLEXPORT void FBroDoubleString_Add(CefRefPtr<FBroDoubleString> data, const CefString& key, const CefString& value);
DLLEXPORT int FBroDoubleString_Size(CefRefPtr<FBroDoubleString> data);
DLLEXPORT void FBroDoubleString_SetCurrentData(CefRefPtr<FBroDoubleString> data, const CefString& value);
DLLEXPORT CefRefPtr<FBroString> FBroDoubleString_FindKeyValue(CefRefPtr<FBroDoubleString> data, const CefString& key);
DLLEXPORT bool FBroDoubleString_Delete(CefRefPtr<FBroDoubleString> data, const CefString& key);
DLLEXPORT void FBroDoubleString_Clear(CefRefPtr<FBroDoubleString> data);

class FBroCefStringList : public virtual CefBaseRefCounted
{
public:
	virtual int Size() = 0;
	virtual void ToBegin() = 0;
	virtual void ToEnd() = 0;
	virtual bool ToNext() = 0;
	virtual void Add(const CefString& value) = 0;
	virtual bool Delete(const CefString& value) = 0;
	virtual void Clear() = 0;
	virtual void SetCurrentData(const CefString& value) = 0;
	virtual CefString GetValue(int id) = 0;
	virtual CefString GetCurrentData_Value() = 0;
	virtual std::vector<CefString>& GetData() = 0;
	virtual void SetData(std::vector<CefString> indata) = 0;
};

DLLEXPORT CefRefPtr<FBroCefStringList> FBroCefStringList_Creat(const std::vector<CefString>& data);

DLLEXPORT CefRefPtr<FBroCefStringList> FBroCefStringList_Creat();
DLLEXPORT int FBroCefStringList_Size(CefRefPtr<FBroCefStringList> data);
DLLEXPORT void FBroCefStringList_ToBegin(CefRefPtr<FBroCefStringList> data);
DLLEXPORT void FBroCefStringList_ToEnd(CefRefPtr<FBroCefStringList> data);
DLLEXPORT bool FBroCefStringList_ToNext(CefRefPtr<FBroCefStringList> data);
DLLEXPORT void FBroCefStringList_Clear(CefRefPtr<FBroCefStringList> data);
DLLEXPORT void FBroCefStringList_Add(CefRefPtr<FBroCefStringList> data, const CefString& value);
DLLEXPORT void FBroCefStringList_SetCurrentData(CefRefPtr<FBroCefStringList> data, const CefString& value);
DLLEXPORT CefRefPtr<FBroString> FBroCefStringList_GetValue(CefRefPtr<FBroCefStringList> data, int id);
DLLEXPORT CefRefPtr<FBroString> FBroCefStringList_GetCurrentData_Value(CefRefPtr<FBroCefStringList> data);
DLLEXPORT bool FBroCefStringList_Delete(CefRefPtr<FBroCefStringList> data, const CefString& value);

// 内部调用
DLLEXPORT std::vector<CefString>& FBroCefStringList_GetData(CefRefPtr<FBroCefStringList> data);

class FBroPostDataList : public virtual CefBaseRefCounted
{
public:
	virtual int Size() = 0;
	virtual void ToBegin() = 0;
	virtual void ToEnd() = 0;
	virtual bool ToNext() = 0;
	virtual void Clear() = 0;
	virtual void Add(CefRefPtr<CefPostDataElement> value) = 0;
	virtual CefRefPtr<CefPostDataElement> GetValue(int id) = 0;
	virtual CefRefPtr<CefPostDataElement> GetCurrentData_Value() = 0;
};

DLLEXPORT CefRefPtr<FBroPostDataList> FBroPostDataList_Creat(const CefPostData::ElementVector& data);

DLLEXPORT int FBroPostDataList_Size(CefRefPtr<FBroPostDataList> data);
DLLEXPORT void FBroPostDataList_ToBegin(CefRefPtr<FBroPostDataList> data);
DLLEXPORT void FBroPostDataList_ToEnd(CefRefPtr<FBroPostDataList> data);
DLLEXPORT bool FBroPostDataList_ToNext(CefRefPtr<FBroPostDataList> data);
DLLEXPORT void FBroPostDataList_Clear(CefRefPtr<FBroPostDataList> data);
DLLEXPORT void FBroPostDataList_Add(CefRefPtr<FBroPostDataList> data, CefRefPtr<CefPostDataElement> value);
DLLEXPORT CefRefPtr<CefPostDataElement> FBroPostDataList_GetValue(CefRefPtr<FBroPostDataList> data, int id);
DLLEXPORT CefRefPtr<CefPostDataElement> FBroPostDataList_GetCurrentData(CefRefPtr<FBroPostDataList> data);


class FBroDraggableRegion : public virtual CefBaseRefCounted
{
public:
	virtual int Size()=0;
	virtual void ToBegin()=0;
	virtual void ToEnd()=0;
	virtual bool ToNext()=0;
	virtual void Clear()=0;
	virtual void Add(CefDraggableRegion value)=0;
	virtual CefDraggableRegion GetValue(int id)=0;
	virtual CefDraggableRegion GetCurrentData_Value()=0;
};

DLLEXPORT CefRefPtr<FBroDraggableRegion> FBroDraggableRegion_Creat(const std::vector<CefDraggableRegion>& data);

DLLEXPORT CefRefPtr<FBroDraggableRegion> FBroDraggableRegion_Creat();
DLLEXPORT int FBroDraggableRegion_Size(CefRefPtr<FBroDraggableRegion> data);
DLLEXPORT void FBroDraggableRegion_ToBegin(CefRefPtr<FBroDraggableRegion> data);
DLLEXPORT void FBroDraggableRegion_ToEnd(CefRefPtr<FBroDraggableRegion> data);
DLLEXPORT bool FBroDraggableRegion_ToNext(CefRefPtr<FBroDraggableRegion> data);
DLLEXPORT void FBroDraggableRegion_Clear(CefRefPtr<FBroDraggableRegion> data);
DLLEXPORT void FBroDraggableRegion_Add(CefRefPtr<FBroDraggableRegion> data, POINT_DRAGGABLEREGION value);
DLLEXPORT void FBroDraggableRegion_GetValue(CefRefPtr<FBroDraggableRegion> data, int id, POINT_DRAGGABLEREGION retdata);
DLLEXPORT void FBroDraggableRegion_GetCurrentData_Value(CefRefPtr<FBroDraggableRegion> data, POINT_DRAGGABLEREGION retdata);


class FBroX509CertificateList : public virtual CefBaseRefCounted
{
public:
	virtual int Size() = 0;
	virtual void ToBegin() = 0;
	virtual void ToEnd() = 0;
	virtual bool ToNext() = 0;
	virtual void Clear() = 0;
	virtual void Add(CefRefPtr<CefX509Certificate> value) = 0;
	virtual CefRefPtr<CefX509Certificate> GetValue(int id) = 0;
	virtual CefRefPtr<CefX509Certificate> GetCurrentData_Value() = 0;
};

DLLEXPORT CefRefPtr<FBroX509CertificateList> FBroX509CertificateList_Creat(const CefRequestHandler::X509CertificateList& data);
DLLEXPORT CefRefPtr<FBroX509CertificateList> FBroX509CertificateList_Creat();
DLLEXPORT int FBroX509CertificateList_Size(CefRefPtr<FBroX509CertificateList> data);
DLLEXPORT void FBroX509CertificateList_ToBegin(CefRefPtr<FBroX509CertificateList> data);
DLLEXPORT void FBroX509CertificateList_ToEnd(CefRefPtr<FBroX509CertificateList> data);
DLLEXPORT bool FBroX509CertificateList_ToNext(CefRefPtr<FBroX509CertificateList> data);
DLLEXPORT void FBroX509CertificateList_Clear(CefRefPtr<FBroX509CertificateList> data);
DLLEXPORT void FBroX509CertificateList_Add(CefRefPtr<FBroX509CertificateList> data, CefRefPtr<CefX509Certificate> value);
DLLEXPORT CefRefPtr<CefX509Certificate> FBroX509CertificateList_GetValue(CefRefPtr<FBroX509CertificateList> data, int id);
DLLEXPORT CefRefPtr<CefX509Certificate> FBroX509CertificateList_GetCurrentData_Value(CefRefPtr<FBroX509CertificateList> data);



class FBroV8ValueList : public virtual CefBaseRefCounted
{
public:
	virtual int Size() = 0;
	virtual void ToBegin() = 0;
	virtual void ToEnd() = 0;
	virtual bool ToNext() = 0;
	virtual void Clear() = 0;
	virtual void Add(CefRefPtr<CefV8Value> value) = 0;
	virtual CefRefPtr<CefV8Value> GetValue(int id) = 0;
	virtual CefRefPtr<CefV8Value> GetCurrentData_Value() = 0;
	virtual std::vector<CefRefPtr<CefV8Value>> GetData() = 0;
};

DLLEXPORT CefRefPtr<FBroV8ValueList> FBroV8ValueList_Creat(const std::vector<CefRefPtr<CefV8Value>>& data);
DLLEXPORT CefRefPtr<FBroV8ValueList> FBroV8ValueList_Creat();
DLLEXPORT int FBroV8ValueList_Size(CefRefPtr<FBroV8ValueList> data);
DLLEXPORT void FBroV8ValueList_ToBegin(CefRefPtr<FBroV8ValueList> data);
DLLEXPORT void FBroV8ValueList_ToEnd(CefRefPtr<FBroV8ValueList> data);
DLLEXPORT bool FBroV8ValueList_ToNext(CefRefPtr<FBroV8ValueList> data);
DLLEXPORT void FBroV8ValueList_Clear(CefRefPtr<FBroV8ValueList> data);
DLLEXPORT void FBroV8ValueList_Add(CefRefPtr<FBroV8ValueList> data, CefRefPtr<CefV8Value> value);
DLLEXPORT CefRefPtr<CefV8Value> FBroV8ValueList_GetValue(CefRefPtr<FBroV8ValueList> data, int id);
DLLEXPORT CefRefPtr<CefV8Value> FBroV8ValueList_GetCurrentData_Value(CefRefPtr<FBroV8ValueList> data);



class FBroBinaryValueList : public virtual CefBaseRefCounted
{
public:
	virtual int Size() = 0;
	virtual void ToBegin() = 0;
	virtual void ToEnd() = 0;
	virtual bool ToNext() = 0;
	virtual void Clear() = 0;
	virtual void Add(CefRefPtr<CefBinaryValue> value) = 0;
	virtual CefRefPtr<CefBinaryValue> GetValue(int id) = 0;
	virtual CefRefPtr<CefBinaryValue> GetCurrentData_Value() = 0;
};

DLLEXPORT CefRefPtr<FBroBinaryValueList> FBroBinaryValueList_Creat(const std::vector<CefRefPtr<CefBinaryValue>>& data);

DLLEXPORT CefRefPtr<FBroBinaryValueList> FBroBinaryValueList_Creat();
DLLEXPORT int FBroBinaryValueList_Size(CefRefPtr<FBroBinaryValueList> data);
DLLEXPORT void FBroBinaryValueList_ToBegin(CefRefPtr<FBroBinaryValueList> data);
DLLEXPORT void FBroBinaryValueList_ToEnd(CefRefPtr<FBroBinaryValueList> data);
DLLEXPORT bool FBroBinaryValueList_ToNext(CefRefPtr<FBroBinaryValueList> data);
DLLEXPORT void FBroBinaryValueList_Clear(CefRefPtr<FBroBinaryValueList> data);
DLLEXPORT void FBroBinaryValueList_Add(CefRefPtr<FBroBinaryValueList> data, CefRefPtr<CefBinaryValue> value);
DLLEXPORT CefRefPtr<CefBinaryValue> FBroBinaryValueList_GetValue(CefRefPtr<FBroBinaryValueList> data, int id);
DLLEXPORT CefRefPtr<CefBinaryValue> FBroBinaryValueList_GetCurrentData_Value(CefRefPtr<FBroBinaryValueList> data);



class FBroRectValueList : public virtual CefBaseRefCounted
{
public:
	virtual int Size() = 0;
	virtual void ToBegin() = 0;
	virtual void ToEnd() = 0;
	virtual bool ToNext() = 0;
	virtual void Clear() = 0;
	virtual void Add(CefRect value) = 0;
	virtual CefRect GetValue(int id) = 0;
	virtual CefRect GetCurrentData_Value() = 0;
};
DLLEXPORT CefRefPtr<FBroRectValueList> FBroRectValueList_Creat(const std::vector<CefRect>& data);

DLLEXPORT CefRefPtr<FBroRectValueList> FBroRectValueList_Creat();
DLLEXPORT int FBroRectValueList_Size(CefRefPtr<FBroRectValueList> data);
DLLEXPORT void FBroRectValueList_ToBegin(CefRefPtr<FBroRectValueList> data);
DLLEXPORT void FBroRectValueList_ToEnd(CefRefPtr<FBroRectValueList> data);
DLLEXPORT bool FBroRectValueList_ToNext(CefRefPtr<FBroRectValueList> data);
DLLEXPORT void FBroRectValueList_Clear(CefRefPtr<FBroRectValueList> data);
DLLEXPORT void FBroRectValueList_Add(CefRefPtr<FBroRectValueList> data, POINT_RECT value);
DLLEXPORT E_RECT FBroRectValueList_GetValue(CefRefPtr<FBroRectValueList> data, int id);
DLLEXPORT E_RECT FBroRectValueList_GetCurrentData_Value(CefRefPtr<FBroRectValueList> data);


class FBroCompositionUnderlineList : public virtual CefBaseRefCounted
{
public:
	virtual int Size() = 0;
	virtual void ToBegin() = 0;
	virtual void ToEnd() = 0;
	virtual bool ToNext() = 0;
	virtual void Clear() = 0;
	virtual void Add(CefCompositionUnderline value) = 0;
	virtual CefCompositionUnderline GetValue(int id) = 0;
	virtual CefCompositionUnderline GetCurrentData_Value() = 0;
	virtual const std::vector<CefCompositionUnderline>& GetData() = 0;
};

DLLEXPORT CefRefPtr<FBroCompositionUnderlineList> FBroCompositionUnderlineList_Creat(const std::vector<CefCompositionUnderline>& data);
DLLEXPORT CefRefPtr<FBroCompositionUnderlineList> FBroCompositionUnderlineList_Creat();
DLLEXPORT int FBroCompositionUnderlineList_Size(CefRefPtr<FBroCompositionUnderlineList> data);
DLLEXPORT void FBroCompositionUnderlineList_ToBegin(CefRefPtr<FBroCompositionUnderlineList> data);
DLLEXPORT void FBroCompositionUnderlineList_ToEnd(CefRefPtr<FBroCompositionUnderlineList> data);
DLLEXPORT bool FBroCompositionUnderlineList_ToNext(CefRefPtr<FBroCompositionUnderlineList> data);
DLLEXPORT void FBroCompositionUnderlineList_Clear(CefRefPtr<FBroCompositionUnderlineList> data);
DLLEXPORT void FBroCompositionUnderlineList_Add(CefRefPtr<FBroCompositionUnderlineList> data, POINT_COMUNDERLINE value);
DLLEXPORT E_COMUNDERLINE FBroCompositionUnderlineList_GetValue(CefRefPtr<FBroCompositionUnderlineList> data, int id);
DLLEXPORT E_COMUNDERLINE FBroCompositionUnderlineList_GetCurrentData_Value(CefRefPtr<FBroCompositionUnderlineList> data);

//辅助回调设置类
class FBroV8Help : public virtual CefBaseRefCounted {
public:
	virtual void SetV8Value(CefRefPtr<CefV8Value> v8Value) = 0;
	virtual CefRefPtr<CefV8Value> GetV8Value() = 0;
};

DLLEXPORT CefRefPtr<FBroV8Help> FBroV8Help_Creat();
DLLEXPORT void FBroHsV8Help_SetV8Value(CefRefPtr<FBroV8Help> v8Help, CefRefPtr<CefV8Value> v8Value);
DLLEXPORT CefRefPtr<CefV8Value> FBroHsV8Help_SetV8Value(CefRefPtr<FBroV8Help> v8Help);


//class FBroRetBrowser : public virtual CefBaseRefCounted {
//public:
//	virtual CefRefPtr<CefBrowser> GetCurrentBrowser() = 0;
//	virtual CefRefPtr<CefBrowser> GetRetBrowser() = 0;
//	virtual void SetRetBrowser(CefRefPtr<CefBrowser> browser) = 0;
//};


#endif