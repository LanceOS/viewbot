<script lang="ts">
	import Header from '$lib/components/head/Header.svelte';
	import Interface from '$lib/components/landing/Interface.svelte';
	import Links from '$lib/components/landing/Links.svelte';
	import Logs from '$lib/components/landing/Logs.svelte';
</script>

<div class="flex flex-col">
	<Header />
	<main class="mx-auto flex w-full max-w-7xl flex-col gap-12 px-4 py-16">
		<div class="w-full border-b-2 py-2">
			<h1 class="text-3xl">View Generator v1.0</h1>
		</div>

		<Interface />

		<Links />

		<Logs />
	</main>
</div>
