<script lang="ts">
    import type { PageData } from './$types';

    export let data: PageData;
</script>

<div>
    <pre>{JSON.stringify(data.host, null, 2)}</pre>
</div>