<script lang="ts">
    import type { Hosts } from '$lib/types';
    export let hosts: Hosts
</script>

<div class="p-8">
    <div class="text-center mb-8">
        <h1 class="text-3xl font-bold">Total Results</h1>
        <p class="text-3xl mt-2">{hosts.total.toLocaleString()}</p>
    </div>

    <div class="grid grid-cols-1 gap-8">
        <!-- Top Cities -->
        <div>
            <h2 class="text-xl font-semibold mb-4">Top Countries</h2>
            <ul>
                {#each hosts.top_countries as top_country}
                    <li class="flex justify-between mb-2">
                        <span>{top_country.value || "Unknown"}</span>
                        <span>{top_country.count.toLocaleString()}</span>
                    </li>
                {/each}
            </ul>
        </div>

        <!-- Top Ports -->
        <div>
            <h2 class="text-xl font-semibold mb-4">Top Ports</h2>
            <ul>
                {#each hosts.top_ports as top_port}
                    <li class="flex justify-between mb-2">
                        <span>{top_port.value}</span>
                        <span>{top_port.count.toLocaleString()}</span>
                    </li>
                {/each}
            </ul>
        </div>
    </div>
</div>