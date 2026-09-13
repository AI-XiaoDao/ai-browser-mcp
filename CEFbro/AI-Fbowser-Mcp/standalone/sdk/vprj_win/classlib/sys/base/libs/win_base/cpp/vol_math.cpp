
// Copyright (C) Recursion Company. All rights reserved.

#include "../vol_base.h"

BOOL_P CMRect::Intersect (const CMRect& rt, CMRect* prtIntersect) const
{
    ASSERT_RW_DATA_OR_NULL (prtIntersect);

    if (IsEmpty () || rt.IsEmpty () ||
            left >= rt.right || right <= rt.left ||
            top >= rt.bottom || bottom <= rt.top)
    {
        if (prtIntersect != NULL)
            prtIntersect->SetEmpty ();
        return FALSE;
    }

    if (prtIntersect != NULL)
    {
        prtIntersect->left = MAX (left, rt.left);
        prtIntersect->top = MAX (top, rt.top);
        prtIntersect->right = MIN (right, rt.right);
        prtIntersect->bottom = MIN (bottom, rt.bottom);
        ASSERT (prtIntersect->IsEmpty () == FALSE);
    }

    return TRUE;
}

void CMRect::Add (const CMRect& rt)
{
    if (rt.IsEmpty () == FALSE)
    {
        if (IsEmpty ())
        {
            Set (rt);
        }
        else
        {
            left = MIN (left, rt.left);
            top = MIN (top, rt.top);
            right = MAX (right, rt.right);
            bottom = MAX (bottom, rt.bottom);
        }
    }
}

void CFRect::Add (const CFRect& rt)
{
    if (rt.IsEmpty () == FALSE)
    {
        if (IsEmpty ())
        {
            Set (rt);
        }
        else
        {
            left = MIN (left, rt.left);
            top = MIN (top, rt.top);
            right = MAX (right, rt.right);
            bottom = MAX (bottom, rt.bottom);
        }
    }
}

BOOL_P CFRect::Intersect (const CFRect& rt, CFRect* prtIntersect) const
{
    ASSERT_RW_DATA_OR_NULL (prtIntersect);

    if (IsEmpty () || rt.IsEmpty () ||
            left >= rt.right - NEAR_ZERO_FLOAT ||
            right <= rt.left + NEAR_ZERO_FLOAT ||
            top >= rt.bottom - NEAR_ZERO_FLOAT ||
            bottom <= rt.top + NEAR_ZERO_FLOAT)
    {
        if (prtIntersect != NULL)
            prtIntersect->SetEmpty ();
        return FALSE;
    }

    if (prtIntersect != NULL)
    {
        prtIntersect->left = MAX (left, rt.left);
        prtIntersect->top = MAX (top, rt.top);
        prtIntersect->right = MIN (right, rt.right);
        prtIntersect->bottom = MIN (bottom, rt.bottom);
        ASSERT (prtIntersect->IsEmpty () == FALSE);
    }

    return TRUE;
}
