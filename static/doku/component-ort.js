'use strict';

export async function get_ort(ort_id)
{
    const o = await fetch("/doku/Ort/" + ort_id);
    return o.json();
}