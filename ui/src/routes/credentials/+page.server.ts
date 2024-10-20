import * as api from '$lib/api';
import type { Credential } from '$lib/types';

const getCredentials = async (skip?: FormDataEntryValue | number, limit?: FormDataEntryValue | number) => {
	const credentials = await api.get(`credentials?skip=${skip}&limit=${limit}`);
	return credentials as Credential[];
};

/** @type {import('./$types').PageServerLoad} */
export async function load({ url }) {
    
	return {
		"credentials": await getCredentials(
            url.searchParams.get('skip') || 0,
		    url.searchParams.get('limit') || 10 //locals.site.settings.paginationLimit
        )
	};
}
