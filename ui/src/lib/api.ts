import { env } from '$env/dynamic/public';
import type { Count, Host } from './types';

export const base = `${env.PUBLIC_API_URL}/api/v1`;

type SendParameters = {
	method: string;
	path: string;
	data?: object;
};

async function send({ method, path, data }: SendParameters) {
	const headers = new Headers();

	if (data) {
		headers.set('Content-Type', 'application/json');
	}

	const opts: RequestInit = {
		method,
		headers,
		body: data ? JSON.stringify(data) : undefined
	};

	const res = await fetch(`${base}/${path}`, opts);
	if (res.ok || res.status === 422) {
		const text = await res.text();
		return text ? JSON.parse(text) : {};
	}
}

export function get(path: string) {
	return send({ method: 'GET', path });
}

export function del(path: string) {
	return send({ method: 'DELETE', path });
}

export function post(path: string, data: object) {
	return send({ method: 'POST', path, data });
}

export function put(path: string, data: object) {
	return send({ method: 'PUT', path, data });
}


//
//
//

export const getHost = async (ip: string) => {
	const host = await get(`host/${ip}`);
	return host as Host;
};

export const getHosts = async (query?: string, skip?: number, limit?: number) => {
	const params = new URLSearchParams();

	if (query !== undefined) params.append('query', query);
	if (skip !== undefined) params.append('skip', skip.toString());
	if (limit !== undefined) params.append('limit', limit.toString());

	const hosts = await get(`host/search?${params.toString()}`);
	return hosts as Host[];
  };


export const getCounts = async (query?: string, facet?: string) => {
	const params = new URLSearchParams();

	if (query !== undefined) params.append('query', query);
	if (facet !== undefined) params.append('facet', facet);

	const counts = await get(`host/count?${params.toString()}`);
	return counts as Count;
  };
