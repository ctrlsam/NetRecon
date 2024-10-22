<script lang="ts">
    import type { PageData } from './$types';
    import HostSidebar from '$lib/components/HostSidebar.svelte';
    import HostItem from '$lib/components/HostItem.svelte';

    export let data: PageData;
    console.log(data)
</script>

<div class="flex">
    <div class="w-1/4 h-screen border-r">
        <HostSidebar counts={data.counts} />
    </div>
    <div class="w-full">
        {#each data.hosts as host}
            <HostItem host={host}/>
        {/each}
    </div>
</div>
