#pragma once
#ifndef FBROWSER_EVALUECONTROL_H_
#define FBROWSER_EVALUECONTROL_H_

class EClassStruct;

#ifndef _FBROELIB
DLLEXPORT void TEXPORTS FBroPopupFeaturesToEPopupFeatures(HANDLE popupFeatures, cef_popup_features_t* e_popupFeatures);
DLLEXPORT void TEXPORTS FBroWindowInfoToEWindowInfo(HANDLE windowInfo, PTELIB_WINDOWS_INFO e_windowInfo);
DLLEXPORT void TEXPORTS FBroBrowserSetToEBrowserSet(HANDLE BrowserSet, FBroBrowserSetting* EBrowserSet);


DLLEXPORT void TEXPORTS FBroEPopupFeaturesToPopupFeatures(HANDLE popupFeatures, cef_popup_features_t* e_popupFeatures);
DLLEXPORT void TEXPORTS FBroEWindowInfoToWindowInfo(HANDLE windowInfo, PTELIB_WINDOWS_INFO e_windowInfo);
DLLEXPORT void TEXPORTS FBroEBrowserSetToBrowserSet(HANDLE BrowserSet, FBroBrowserSetting* EBrowserSet);



//DLLEXPORT void TEXPORTS FBroReleaseEBrowserSet(FBroBrowserSetting* browserset);
DLLEXPORT void TEXPORTS FBroReleaseEWindowInfo(PTELIB_WINDOWS_INFO windowInfo);


DLLEXPORT void TEXPORTS FBroPointToKeyEvent(HANDLE indata, POINT_KEYEVENT retdata);
DLLEXPORT void TEXPORTS FBroPonitToOSEvent(HANDLE indata, POINT_OSEVENT retdata);

DLLEXPORT size_t TEXPORTS FBroPonitToCharArrary(HANDLE indata, char** retdata, int count, int size);

DLLEXPORT void TEXPORTS FBroPonitToRect(HANDLE indata, cef_rect_t* retdata);

DLLEXPORT void TEXPORTS FBroPonitToDraggableRegion(HANDLE indata, POINT_DRAGGABLEREGION retdata);

DLLEXPORT void TEXPORTS FBroPonitToERect(HANDLE indata, POINT_RECT retdata);
DLLEXPORT void TEXPORTS FBroPonitToCefRect(HANDLE indata, CefRect* retdata);

DLLEXPORT void TEXPORTS FBroPonitToEScreenInfo(HANDLE indata, POINT_SCREENINFO retdata);
DLLEXPORT void TEXPORTS FBroPonitToCefScreenInfo(HANDLE indata, CefScreenInfo* retdata);
DLLEXPORT size_t TEXPORTS FBroPonitToERectList(HANDLE indata, POINT_RECT retdata, int count);

DLLEXPORT void TEXPORTS FBroPonitToECursorInfo(CefCursorInfo* indata, POINT_CURSORINFO retdata);
DLLEXPORT void TEXPORTS FBroPonitToERange(HANDLE indata, POINT_RANGE retdata);

DLLEXPORT void TEXPORTS FBroGetV8ListValues(CefV8ValueList* indata, int index, EClassStruct* retObject);


DLLEXPORT void TEXPORTS FBroCefAudioParametersToEAudioParameters(HANDLE cefAudioParameters, POINT_E_AudioParameters e_AudioParameters);
DLLEXPORT void TEXPORTS FBroEAudioParametersToCefAudioParameters(POINT_E_AudioParameters e_AudioParameters, HANDLE cefAudioParameters);

DLLEXPORT void TEXPORTS FBroPonitToEAcceleratedPaintInfo(HANDLE indata, POINT_ACCELERATED_PAINT_INFO retdata);

#endif // !_FBROELIB




#endif