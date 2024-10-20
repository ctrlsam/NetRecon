import * as api from '$lib/api';
import type { Host } from '$lib/types';

const getHost = async (ip: string) => {
	const host = await api.get(`hosts/${ip}`);
	return host as Host;
};

/** @type {import('./$types').PageServerLoad} */
export async function load({ params }) {
	return {
		"host": await getHost(params.ip)
	};
}
