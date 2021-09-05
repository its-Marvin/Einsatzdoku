'use strict';

export async function get_zug(zug_id)
{
    const o = await fetch("/doku/Zug/" + zug_id);
    return o.json();
}