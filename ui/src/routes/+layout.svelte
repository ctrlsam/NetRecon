<script lang="ts">
	import '../app.postcss';
	import { AppShell, AppBar } from '@skeletonlabs/skeleton';
</script>

<!-- App Shell -->
<AppShell>
	<svelte:fragment slot="header">
		<!-- App Bar -->
		<AppBar>
			<svelte:fragment slot="lead">
				<a href="/" data-sveltekit-reload><strong class="text-xl uppercase">Rigour</strong></a>
			</svelte:fragment>
			<svelte:fragment slot="trail">
				<a href="/" data-sveltekit-reload>Hosts</a>
				<a href="/credentials" data-sveltekit-reload>Credentials</a>
				<a href="/admin" data-sveltekit-reload>Admin</a>
			</svelte:fragment>
		</AppBar>
	</svelte:fragment>
	<!-- Page Route Content -->
	<slot />
</AppShell>
