<script lang="ts">
    import type { Host } from '$lib/types';
    export let host: Host;

    function isVulnerable(){
        return host.scans.some(scan => scan.vulnerabilities && scan.vulnerabilities.length > 0);
    }
</script>

<div class="bg-red-900 rounded mb-3 pl-10 h-32 p-2">
    {#if host.timestamp}
        <p>{host.timestamp}</p>
    {/if}

    <div class="flex">
        <a href="/host/{host.saddr}"><p class="text-2xl">{host.saddr}</p></a>

        {#each host.scans as scan}
            {#if scan.data?.http?.status == "success"}
                <a href="http://{host.saddr}:{scan.sport}" target="_blank"><p>View Site</p></a>
            {/if}
        {/each }
    </div>

    <!-- Show port -->
    <div class="flex">
        {#each host.scans as scan}
            <div class="bg-slate-600 px-3 py-1">
                <p>{scan.sport}</p>
            </div>
        {/each}
    </div>

    {#if isVulnerable()}
        <p class="text-2xl">Vulnerable</p>
    {/if}

</div>