import * as api from '$lib/api';

/** @type {import('./$types').PageServerLoad} */
export async function load({ params }) {
	return await api.getHost(params.ip);
}
