<script lang="ts">
	import Icon from '@iconify/svelte';

	let isActive = $state(false);

	let processes = $state(0);

	let viewProcessWarning = $state(false);
</script>

<section class="flex items-center justify-between gap-6">
	<div class="flex items-center gap-8">
		<button type="button" class="btn-start">Activate</button>
		<button type="button" class="btn-stop">Deactivate</button>
		{#if isActive}
			<p class="text-base-content text-lg">
				Currently running: <span class="text-success text-xl font-bold">TRUE</span>
			</p>
		{:else}
			<p class="text-base-content text-lg">
				Currently running: <span class="text-error text-xl font-bold">FALSE</span>
			</p>
		{/if}
	</div>

	<div class="relative flex items-center gap-4">
		<p class="text-lg">Processes: {processes}</p>

		<div class="relative flex flex-col items-center">
			<Icon
				icon="material-symbols:info-outline"
				class="text-neutral cursor-pointer text-2xl"
				onmouseover={() => (viewProcessWarning = true)}
				onmouseleave={() => (viewProcessWarning = false)}
			/>

			{#if viewProcessWarning}
				<p
					class="bg-neutral text-neutral-content absolute top-full z-10 mt-2 w-64 rounded p-4 shadow-md duration-200"
				>
					This shows how many threads you have set to run at a time. Each thread is how many videos
					will be viewed at once. The more threads the slower your computer will run.
				</p>
			{/if}
		</div>
	</div>
</section>
