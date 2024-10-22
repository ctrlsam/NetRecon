<script lang="ts">
    import type { Host } from '$lib/types';
    export let host: Host;

    if (host.banners.http) {
        console.log(host.banners.http);
    }
</script>

<div class="bg-red-900 rounded mb-3 pl-10 h-32 p-2">
    {#if host.updated_at}
        <p class="text-slate-200 text-xs">{host.updated_at}</p>
    {/if}

    <div class="flex-col py-3">
        <a href="/host/{host.ip}"><p class="text-2xl">{host.ip}</p></a>

        <div class="flex pt-2">
            {#each Object.entries(host.banners) as [service, details]}
                <div class="bg-slate-600 px-3 py-1">
                    <p>{service} ({details.port})</p>
                </div>
            {/each}
        </div>

        <!-- {#each host.banner as scan}
            {#if scan.data?.http?.status == "success"}
                <a href="http://{host.ip}:{scan.sport}" target="_blank"><p>View Site</p></a>
            {/if}
        {/each } -->
    </div>

    <!-- Show port -->
    <!-- <div class="flex">
        {#each host.scans as scan}
            <div class="bg-slate-600 px-3 py-1">
                <p>{scan.sport}</p>
            </div>
        {/each}
    </div> -->



</div>
