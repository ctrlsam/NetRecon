<script lang="ts">
    import type { PageData } from './$types';

    export let data: PageData;
</script>

<div>
    {#each data.credentials as credential}
        <pre>{JSON.stringify(credential, null, 2)}</pre>
    {/each}
</div>