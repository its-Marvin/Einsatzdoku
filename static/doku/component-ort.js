'use strict';

export async function get_ort(ort_id)
{
    const o = await fetch("/Ort/" + ort_id);
    return o.json();
}