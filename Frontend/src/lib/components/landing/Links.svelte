<script lang="ts">
	import Icon from '@iconify/svelte';
	import { onMount } from 'svelte';

	interface Link {
		id: number;
		href: string;
	}

	let linkErr = $state(false);

	let newLink: string = $state('');
	let links: Link[] = $state([]);

	const addNewLink = () => {
		if (
			!newLink.includes('https://www.youtube.com/shorts/') ||
			newLink === 'https://www.youtube.com/shorts/'
		) {
			return (linkErr = true);
		}

		const obj: Link = { id: links[links.length - 1].id + 1, href: newLink };
		links = [...links, obj];

		newLink = '';
	};

	const removeLink = (id: number) => {
		links = links.filter((link) => link.id !== id);
	};

	$effect(() => {
		newLink;
		linkErr = false;
	});

	const getLinks = () => {
		return [
			{
				id: 1,
				href: 'https://www.youtube.com/shorts/oEO9IBVICeY'
			},
			{
				id: 2,
				href: 'https://www.youtube.com/shorts/oEO9IBVICeY'
			},
			{
				id: 2,
				href: 'https://www.youtube.com/shorts/oEO9IBVICeY'
			},
			{
				id: 3,
				href: 'https://www.youtube.com/shorts/oEO9IBVICeY'
			},
			{
				id: 4,
				href: 'https://www.youtube.com/shorts/oEO9IBVICeY'
			},
			{
				id: 5,
				href: 'https://www.youtube.com/shorts/oEO9IBVICeY'
			}
		];
	};

	onMount(() => {
		links = getLinks();
	});
</script>

<section class="flex flex-col gap-6">
	<h2 class="text-2xl">Links</h2>

	<div class="flex w-full flex-col gap-8">
		<div class="bg-base-300 flex flex-col gap-4 p-4">
			<div class="flex justify-between">
				<label for="shortLink">New Link <span class="text-error">*</span></label>

				{#if linkErr}
					<p class="text-error">Link must be a youtube short!</p>
				{/if}
			</div>

			<div class="flex h-10 justify-between">
				<input
					type="text"
					name="shortLink"
					placeholder="https://www.youtube.com/shorts/?"
					class="focus:outline-0"
					bind:value={newLink}
				/>
				<button
					type="button"
					class={`btn ${newLink ? 'flex' : 'hidden'}`}
					disabled={!newLink}
					onclick={addNewLink}>Add Link</button
				>
			</div>
		</div>

		<div class="flex h-72 flex-col gap-8 overflow-y-auto overflow-x-hidden border p-6">
			{#each links as link}
				<div class="flex items-center justify-between">
					<p class="text-neutral">{link.href}</p>
					<button type="button" class="cursor-pointer" onclick={() => removeLink(link.id)}
						><Icon icon="clarity:trash-line" class="text-error text-xl" /></button
					>
				</div>
			{/each}
		</div>
	</div>
</section>
