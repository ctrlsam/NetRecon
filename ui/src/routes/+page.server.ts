import * as api from '$lib/api';
import type { Hosts } from '$lib/types';

const getHosts = async (skip?: FormDataEntryValue, limit?: FormDataEntryValue) => {
	const hosts = await api.get('hosts?skip=' + skip + '&limit=' + limit);
	return hosts as Hosts;
};

/** @type {import('./$types').PageServerLoad} */
export async function load({ locals, url }) {
	return await getHosts(
		url.searchParams.get('skip') || 0,
		url.searchParams.get('limit') || 10 //locals.site.settings.paginationLimit
	);
}
