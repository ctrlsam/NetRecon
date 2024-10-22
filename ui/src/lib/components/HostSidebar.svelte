<script lang="ts">
    import type { Count } from '$lib/types';
    export let counts: Count
</script>

<div class="p-8">
    <div class="text-center mb-8">
        <h1 class="text-3xl font-bold">Total Results</h1>
        <p class="text-3xl mt-2">{counts.total.toLocaleString()}</p>
    </div>

    <div class="grid grid-cols-1 gap-8">

        {#if counts.facets.location_country_name}
        <div>
            <h2 class="text-xl font-semibold mb-4">Top Countries</h2>
            <ul>
                {#each counts.facets.location_country_name as country}
                    <li class="flex justify-between mb-2">
                        <span>{country._id || "Unknown"}</span>
                        <span>{country.count.toLocaleString()}</span>
                    </li>
                {/each}
            </ul>
        </div>
        {/if}


        <!-- Top Ports -->
        <!-- TODO: Need to update API to allow nested query, e.g banners.*.port -->
    </div>
</div>
