#pragma once

#ifndef VIEWPORT
typedef struct VIEWPORT
{
	int x;
	int y;
	int width;
	int height;
	int scale;
}*VIEWPORT_POINT;
#endif

#ifndef E_DEV_TOUCHPOINT
typedef struct E_DEV_TOUCHPOINT {
	int x;//ºá×ø±ê
	int y;//×Ý×ø±ê
	int radiusX;//ºá°ë¾¶
	int radiusY;//×Ý°ë¾¶
	int rotationAngle;//Ðý×ª½Ç¶È
	int force;//Ñ¹Á¦
	int id;
}*POINT_DEV_TOUCHPOINT;
#endif

#ifndef M_POINTER
#ifdef _WIN64
typedef long long M_POINTER;
#else
typedef long M_POINTER;
#endif // _WIN64
#endif