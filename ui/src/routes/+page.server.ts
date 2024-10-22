import * as api from '$lib/api';

/** @type {import('./$types').PageServerLoad} */
export async function load({ url }) {
  const queryParam = url.searchParams.get('query');
  const skipParam = url.searchParams.get('skip');
  const limitParam = url.searchParams.get('limit');

  const query = queryParam !== null ? queryParam : undefined;
  const skip = skipParam !== null ? Number(skipParam) : 0;
  const limit = limitParam !== null ? Number(limitParam) : 10;

  return {
    hosts: await api.getHosts(query, skip, limit),
    counts: await api.getCounts(query, 'location.country_name,port'),
  };
}
