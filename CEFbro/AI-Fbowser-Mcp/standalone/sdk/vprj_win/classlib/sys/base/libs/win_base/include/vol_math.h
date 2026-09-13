
// Copyright (C) Recursion Company. All rights reserved.

#ifndef __VOL_MATH_H__
#define __VOL_MATH_H__

#ifdef _PF_WINDOWS
    #define _CMSize  SIZE
    class CMSize : public tagSIZE
    {
#else
    #define _CMSize  CMSize
    class CMSize : public CVolCommonBase
    {
    public:
        INT cx, cy;
#endif

    public:
        inline_ CMSize ()
        {
        }

        inline_ CMSize (const INT cxSize, const INT cySize)
        {
            cx = cxSize;
            cy = cySize;
        }

        inline_ CMSize (const _CMSize& size)
        {
            cx = size.cx;
            cy = size.cy;
        }

    public:
        inline_ const CMSize& operator= (const _CMSize& size)
        {
            cx = size.cx;
            cy = size.cy;
            return *this;
        }

        inline_ void Set (const INT cxSize, const INT cySize)
        {
            cx = cxSize;
            cy = cySize;
        }

        inline_ void Set (const _CMSize& size)
        {
            cx = size.cx;
            cy = size.cy;
        }

        inline_ void Zero ()
        {
            cx = cy = 0;
        }

        inline_ BOOL_P operator== (const _CMSize& size) const
        {
            return cx == size.cx && cy == size.cy;
        }

        inline_ BOOL_P operator!= (const _CMSize& size) const
        {
            return cx != size.cx || cy != size.cy;
        }

        inline_ void operator+= (const _CMSize& size)
        {
            cx += size.cx;
            cy += size.cy;
        }

        inline_ void operator-= (const _CMSize& size)
        {
            cx -= size.cx;
            cy -= size.cy;
        }

        inline_ void operator*= (const INT n)
        {
            cx *= n;
            cy *= n;
        }

        inline_ void operator/= (const INT n)
        {
            ASSERT (n != 0);
            cx /= n;
            cy /= n;
        }

        inline_ CMSize operator+ (const _CMSize& size) const
        {
            return CMSize (cx + size.cx, cy + size.cy);
        }

        inline_ CMSize operator- (const _CMSize& size) const
        {
            return CMSize (cx - size.cx, cy - size.cy);
        }

        inline_ CMSize operator* (const INT n) const
        {
            return CMSize (cx * n, cy * n);
        }

        inline_ CMSize operator/ (const INT n) const
        {
            ASSERT (n != 0);
            return CMSize (cx / n, cy / n);
        }

        inline_ CMSize operator- () const
        {
            return CMSize (-cx, -cy);
        }
    };

//----------------------------------------------------------

#ifdef _PF_WINDOWS
    #define _CMPoint  POINT
    class CMPoint : public tagPOINT
    {
#else
    #define _CMPoint  CMPoint
    class CMPoint : public CVolCommonBase
    {
    public:
        INT x, y;
#endif

    public:
        inline_ CMPoint ()
        {
        }

        inline_ CMPoint (const INT xPos, const INT yPos)
        {
            x = xPos;
            y = yPos;
        }

        inline_ CMPoint (const _CMPoint& pt)
        {
            x = pt.x;
            y = pt.y;
        }

    public:
        inline_ const CMPoint& operator= (const _CMPoint& pt)
        {
            x = pt.x;
            y = pt.y;
            return *this;
        }

        inline_ void Zero ()
        {
            x = y = 0;
        }

        inline_ void Set (const INT xPos, const INT yPos)
        {
            x = xPos;
            y = yPos;
        }

        inline_ void Set (const _CMPoint& pt)
        {
            x = pt.x;
            y = pt.y;
        }

        inline_ BOOL_P IsEqual (const _CMPoint& pt) const
        {
            return (x == pt.x && y == pt.y);
        }

        inline_ BOOL_P operator== (const _CMPoint& pt) const
        {
            return IsEqual (pt);
        }

        inline_ BOOL_P operator!= (const _CMPoint& pt) const
        {
            return (IsEqual (pt) == FALSE);
        }

        inline_ void operator+= (const _CMPoint& pt)
        {
            x += pt.x;
            y += pt.y;
        }

        inline_ void operator-= (const _CMPoint& pt)
        {
            x -= pt.x;
            y -= pt.y;
        }

        inline_ CMPoint operator+ (const _CMPoint& pt) const
        {
            return CMPoint (x + pt.x, y + pt.y);
        }

        inline_ CMPoint operator- (const _CMPoint& pt) const
        {
            return CMPoint (x - pt.x, y - pt.y);
        }

        inline_ void operator+= (const CMSize& size)
        {
            x += size.cx;
            y += size.cy;
        }

        inline_ void operator-= (const CMSize& size)
        {
            x -= size.cx;
            y -= size.cy;
        }

        inline_ CMPoint operator+ (const CMSize& size) const
        {
            return CMPoint (x + size.cx, y + size.cy);
        }

        inline_ CMPoint operator- (const CMSize& size) const
        {
            return CMPoint (x - size.cx, y - size.cy);
        }

        inline_ CMPoint operator- () const
        {
            return CMPoint (-x, -y);
        }
    };

//----------------------------------------------------------

#ifdef _PF_WINDOWS
    #define _CMRect  RECT
    class CMRect : public tagRECT
    {
#else
    #define _CMRect  CMRect
    class CMRect : public CVolCommonBase
    {
    public:
        INT left, top, right, bottom;
#endif

    public:
        inline_ CMRect ()
        {
        }

        inline_ CMRect (const INT nLeft, const INT nTop, const INT nRight, const INT nBottom)
        {
            Set (nLeft, nTop, nRight, nBottom);
        }

        inline_ CMRect (const _CMRect& rt)
        {
            Set (rt);
        }

        inline_ CMRect (const _CMRect* prt)
        {
            Set (prt);
        }

        inline_ CMRect (const CMPoint& point, const CMSize& size)
        {
            Set (point, size);
        }

        inline_ CMRect (const CMPoint& ptTopLeft, const CMPoint& ptBottomRight)
        {
            Set (ptTopLeft, ptBottomRight);
        }

        //----------------------------------------------------

        inline_ void SetEmpty ()
        {
            left = top = right = bottom = 0;
        }

        inline_ void Zero ()
        {
            left = top = right = bottom = 0;
        }

        inline_ void Set (const INT n)
        {
            left = top = right = bottom = n;
        }

        inline_ void Set (const INT nLeft, const INT nTop, const INT nRight, const INT nBottom)
        {
            left = nLeft;
            top = nTop;
            right = nRight;
            bottom = nBottom;
        }

        inline_ void Set (const _CMRect& rt)
        {
            left = rt.left;
            top = rt.top;
            right = rt.right;
            bottom = rt.bottom;
        }

        inline_ void Set (const _CMRect* prt)
        {
            ASSERT (prt != NULL);
            left = prt->left;
            top = prt->top;
            right = prt->right;
            bottom = prt->bottom;
        }

        inline_ void Set (const CMPoint& point, const CMSize& size)
        {
            left = point.x;
            top = point.y;
            right = point.x + size.cx;
            bottom = point.y + size.cy;
        }

        inline_ void Set (const CMPoint& ptTopLeft, const CMPoint& ptBottomRight)
        {
            left = ptTopLeft.x;
            top = ptTopLeft.y;
            right = ptBottomRight.x;
            bottom = ptBottomRight.y;
        }

        inline_ void SetLeftTop (const INT nLeft, const INT nTop)
        {
            left = nLeft;
            top = nTop;
        }

        inline_ void SetLeftTop (const CMPoint& pt)
        {
            left = pt.x;
            top = pt.y;
        }

        inline_ void SetSize (const INT nWidth, const INT nHeight)
        {
            right = left + nWidth;
            bottom = top + nHeight;
        }

        inline_ void SetSize (const CMSize& size)
        {
            right = left + size.cx;
            bottom = top + size.cy;
        }

        //----------------------------------------------------

        inline_ void XOffset (const INT xOffset)
        {
            left += xOffset;
            right += xOffset;
        }

        inline_ void YOffset (const INT yOffset)
        {
            top += yOffset;
            bottom += yOffset;
        }

        inline_ void Offset (const INT xOffset, const INT yOffset)
        {
            left += xOffset;
            right += xOffset;
            top += yOffset;
            bottom += yOffset;
        }

        inline_ void Offset (const _CMPoint& ptOffset)
        {
            Offset (ptOffset.x, ptOffset.y);
        }

        inline_ void Inflate (const INT x, const INT y)
        {
            left -= x;
            right += x;
            top -= y;
            bottom += y;
        }

        inline_ void Deflate (const INT x, const INT y)
        {
            left += x;
            right -= x;
            top += y;
            bottom -= y;
        }

        // 基于指定矩形扩充本矩形
        void Add (const CMRect& rt);

        inline_ const CMRect& operator= (const _CMRect& rt)
        {
            Set (rt);
            return *this;
        }

        //----------------------------------------------------

        inline_ CMRect operator- () const
        {
            return CMRect (-left, -top, -right, -bottom);
        }

        inline_ CMRect operator* (const DOUBLE dbScale) const
        {
            return CMRect (IntMulDouble (left, dbScale), IntMulDouble (top, dbScale),
                    IntMulDouble (right, dbScale), IntMulDouble (bottom, dbScale));
        }

        inline_ CMRect operator/ (const DOUBLE dbScale) const
        {
            return CMRect (IntDivDouble (left, dbScale), IntDivDouble (top, dbScale),
                    IntDivDouble (right, dbScale), IntDivDouble (bottom, dbScale));
        }

        inline_ CMRect& operator*= (const DOUBLE dbScale)
        {
            left = IntMulDouble (left, dbScale);
            top = IntMulDouble (top, dbScale);
            right = IntMulDouble (right, dbScale);
            bottom = IntMulDouble (bottom, dbScale);
            return *this;
        }

        inline_ CMRect& operator/= (const DOUBLE dbScale)
        {
            left = IntDivDouble (left, dbScale);
            top = IntDivDouble (top, dbScale);
            right = IntDivDouble (right, dbScale);
            bottom = IntDivDouble (bottom, dbScale);
            return *this;
        }

        inline_ CMRect operator| (const _CMRect& rt) const
        {
            CMRect rtResult;
            rtResult.Add (rt);
            return rtResult;
        }

        inline_ CMRect& operator|= (const _CMRect& rt)
        {
            Add (rt);
            return *this;
        }

        //----------------------------------------------------

        inline_ INT Width () const
        {
            return right - left;
        }

        inline_ INT Height () const
        {
            return bottom - top;
        }

        // 返回矩形面积
        inline_ INT Area () const
        {
            return (bottom - top) * (right - left);
        }

        inline_ CMSize Size () const
        {
            return CMSize (right - left, bottom - top);
        }

        inline_ CMPoint CenterPoint () const
        {
            return CMPoint ((right + left) / 2, (bottom + top) / 2);
        }

        inline_ INT CenterX () const
        {
            return (right + left) / 2;
        }

        inline_ INT CenterY () const
        {
            return (bottom + top) / 2;
        }

        inline_ CMPoint LeftTop () const
        {
            return CMPoint (left, top);
        }

        inline_ CMPoint RightBottom () const
        {
            return CMPoint (right, bottom);
        }

        // 矩形为空则返回真,否则返回假.
        inline_ BOOL_P IsEmpty () const
        {
            return (right <= left || bottom <= top);
        }

        // 通常化
        inline_ void Normalize ()
        {
            if (left > right)
                SWAP_INT (left, right);

            if (top > bottom)
                SWAP_INT (top, bottom);
        }

        inline_ BOOL_P PtInRect (const INT x, const INT y) const
        {
            return x >= left && x < right && y >= top && y < bottom;
        }

        inline_ BOOL_P PtInRect (const _CMPoint& vPos) const
        {
            return vPos.x >= left && vPos.x < right && vPos.y >= top && vPos.y < bottom;
        }

        inline_ void ClampPoint (_CMPoint* pv) const
        {
            ASSERT (pv != NULL);
            ClampPoint ((INT*)&pv->x, (INT*)&pv->y);
        }

        inline_ void ClampPoint (INT* px, INT* py) const
        {
            ASSERT (px != NULL && py != NULL);

            if (*px < left)
                *px = left;
            else if (*px > right)
                *px = right;

            if (*py < top)
                *py = top;
            else if (*py > bottom)
                *py = bottom;
        }

        inline_ BOOL_P IsEqual (const _CMRect& rt) const
        {
            return left == rt.left && top == rt.top &&
                    right == rt.right && bottom == rt.bottom;
        }

        // 如果本矩形和指定矩形相交则返回真且在prtIntersect中返回相交部分,否则返回假.
        // prtIntersect可以指向本对象自身
        BOOL_P Intersect (const CMRect& rt, CMRect* prtIntersect = NULL) const;

        // 如果本矩形位于指定矩形内部则返回真,否则返回假.
        inline_ BOOL_P Inside (const _CMRect& rt) const
        {
            return (left >= rt.left && right <= rt.right &&
                    top >= rt.top && bottom <= rt.bottom);
        }

        // 扩展矩形以包含(x,y)点
        inline_ void Extend (const INT x, const INT y)
        {
            if (x + 1 > right)   right = x + 1;
            if (x < left)        left = x;
            if (y + 1 > bottom)  bottom = y + 1;
            if (y < top)         top = y;
        }

        inline_ BOOL_P operator== (const _CMRect& rt) const
        {
            return IsEqual (rt);
        }

        inline_ BOOL_P operator!= (const _CMRect& rt) const
        {
            return !IsEqual (rt);
        }

        inline_ void MinClip (const INT nMinValue)
        {
            if (left   < nMinValue)  left = nMinValue;
            if (top    < nMinValue)  top = nMinValue;
            if (right  < nMinValue)  right = nMinValue;
            if (bottom < nMinValue)  bottom = nMinValue;
        }

        inline_ void MaxClip (const INT nMaxValue)
        {
            if (left   > nMaxValue)  left = nMaxValue;
            if (top    > nMaxValue)  top = nMaxValue;
            if (right  > nMaxValue)  right = nMaxValue;
            if (bottom > nMaxValue)  bottom = nMaxValue;
        }

        inline_ void Clip (const INT nMinValue, const INT nMaxValue)
        {
            MinClip (nMinValue);
            MaxClip (nMaxValue);
        }
    };

//----------------------------------------------------------

class CFRect : public CVolCommonBase
{
public:
    inline_ CFRect ()
    {
    }

    inline_ CFRect (const FLOAT fLeft, const FLOAT fTop, const FLOAT fRight, const FLOAT fBottom)
    {
        Set (fLeft, fTop, fRight, fBottom);
    }

    inline_ CFRect (const CFRect& rt)
    {
        Set (rt);
    }

    inline_ CFRect (const CFRect* prt)
    {
        Set (prt);
    }

    inline_ CFRect (const _CMRect& rt)
    {
        Set ((FLOAT)rt.left, (FLOAT)rt.top, (FLOAT)rt.right, (FLOAT)rt.bottom);
    }

    //----------------------------------------------------

    inline_ void SetEmpty ()
    {
        left = top = right = bottom = 0.0f;
    }

    inline_ void Set (const FLOAT fLeft, const FLOAT fTop, const FLOAT fRight, const FLOAT fBottom)
    {
        left = fLeft;
        top = fTop;
        right = fRight;
        bottom = fBottom;
    }

    inline_ void Set (const CFRect& rt)
    {
        left = rt.left;
        top = rt.top;
        right = rt.right;
        bottom = rt.bottom;
    }

    inline_ void Set (const CFRect* prt)
    {
        ASSERT_R_DATA (prt);
        left = prt->left;
        top = prt->top;
        right = prt->right;
        bottom = prt->bottom;
    }

    inline_ void Set (const _CMRect& rt)
    {
        left = (FLOAT)rt.left;
        top = (FLOAT)rt.top;
        right = (FLOAT)rt.right;
        bottom = (FLOAT)rt.bottom;
    }

    inline_ void SetMin (const FLOAT fLeft, const FLOAT fTop)
    {
        left = fLeft;
        top = fTop;
    }

    inline_ void SetSize (const FLOAT fWidth, const FLOAT fHeight)
    {
        right = left + fWidth;
        bottom = top + fHeight;
    }

    //----------------------------------------------------

    inline_ void XOffset (const FLOAT fxOffset)
    {
        left += fxOffset;
        right += fxOffset;
    }

    inline_ void YOffset (const FLOAT fyOffset)
    {
        top += fyOffset;
        bottom += fyOffset;
    }

    inline_ void Offset (const FLOAT fxOffset, const FLOAT fyOffset)
    {
        left += fxOffset;
        right += fxOffset;
        top += fyOffset;
        bottom += fyOffset;
    }

    inline_ void Inflate (const FLOAT x, const FLOAT y)
    {
        left -= x;
        right += x;
        top -= y;
        bottom += y;
    }

    inline_ void Deflate (const FLOAT x, const FLOAT y)
    {
        left += x;
        right -= x;
        top += y;
        bottom -= y;
    }

    // 基于指定矩形扩充本矩形
    void Add (const CFRect& rt);

    inline_ const CFRect& operator= (const CFRect& rt)
    {
        Set (rt);
        return *this;
    }

    //----------------------------------------------------

    inline_ CFRect operator- () const
    {
        return CFRect (-left, -top, -right, -bottom);
    }

    inline_ CFRect operator* (const FLOAT f) const
    {
        return CFRect (left * f, top * f, right * f, bottom * f);
    }

    inline_ CFRect operator/ (FLOAT f) const
    {
        ASSERT (IsFloatEqualZero (f) == FALSE);
        f = 1.0f / f;
        return CFRect (left * f, top * f, right * f, bottom * f);
    }

    inline_ CFRect& operator*= (const FLOAT f)
    {
        left *= f;
        top *= f;
        right *= f;
        bottom *= f;
        return *this;
    }

    inline_ CFRect& operator/= (FLOAT f)
    {
        ASSERT (IsFloatEqualZero (f) == FALSE);
        f = 1.0f / f;
        left *= f;
        top *= f;
        right *= f;
        bottom *= f;
        return *this;
    }

    inline_ CFRect operator| (const CFRect& rt) const
    {
        CFRect rtResult;
        rtResult.Add (rt);
        return rtResult;
    }

    inline_ CFRect& operator|= (const CFRect& rt)
    {
        Add (rt);
        return *this;
    }

    //----------------------------------------------------

    inline_ FLOAT Width () const
    {
        return right - left;
    }

    inline_ FLOAT Height () const
    {
        return bottom - top;
    }

    // 返回矩形面积
    inline_ FLOAT Area () const
    {
        return (bottom - top) * (right - left);
    }

    // 矩形为空则返回真,否则返回假.
    inline_ BOOL_P IsEmpty () const
    {
        return (right <= left + NEAR_ZERO_FLOAT || bottom <= top + NEAR_ZERO_FLOAT);
    }

    // 通常化
    inline_ void Normalize ()
    {
        if (left > right)
            SWAP_FLOAT (left, right);

        if (top > bottom)
            SWAP_FLOAT (top, bottom);
    }

    inline_ BOOL_P PtInRect (const FLOAT x, const FLOAT y) const
    {
        return (x >= left - NEAR_ZERO_FLOAT &&
                x < right + NEAR_ZERO_FLOAT &&
                y >= top - NEAR_ZERO_FLOAT &&
                y < bottom + NEAR_ZERO_FLOAT);
    }

    inline_ BOOL_P PtInRect (const FLOAT x, const FLOAT y, const FLOAT fEpsilon) const
    {
        ASSERT (fEpsilon >= 0.0f);
        return (x >= left - fEpsilon &&
                x < right + fEpsilon &&
                y >= top - fEpsilon &&
                y < bottom + fEpsilon);
    }

    inline_ BOOL_P IsEqual (const CFRect& rt) const
    {
        return IsFloatEqual (left, rt.left) && IsFloatEqual (top, rt.top) &&
                IsFloatEqual (right, rt.right) && IsFloatEqual (bottom, rt.bottom);
    }

    // 如果本矩形和指定矩形相交则返回真且在prtIntersect中返回相交部分,否则返回假.
    // prtIntersect可以指向本对象自身
    BOOL_P Intersect (const CFRect& rt, CFRect* prtIntersect = NULL) const;

    // 如果本矩形位于指定矩形内部内部则返回真,否则返回假.
    inline_ BOOL_P Inside (const CFRect& rt) const
    {
        return (left >= rt.left - NEAR_ZERO_FLOAT &&
                right <= rt.right + NEAR_ZERO_FLOAT &&
                top >= rt.top - NEAR_ZERO_FLOAT &&
                bottom <= rt.bottom + NEAR_ZERO_FLOAT);
    }

    inline_ void Extend (const FLOAT x, const FLOAT y)
    {
        if (x > right)   right = x;
        if (x < left)    left = x;
        if (y > bottom)  bottom = y;
        if (y < top)     top = y;
    }

    inline_ BOOL_P operator== (const CFRect& rt) const
    {
        return IsEqual (rt);
    }

    inline_ BOOL_P operator!= (const CFRect& rt) const
    {
        return !IsEqual (rt);
    }

public:
    FLOAT left, top, right, bottom;
};

#endif
