from matplotlib import pyplot as plt
from ase.visualize.plot import plot_atoms
from pymatgen.io.ase import AseAtomsAdaptor
import os
import re
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import numpy as np

class SlabPlotter:
	"""Plot helper: either save each structure immediately (when plot_label provided)
	or accumulate on a grid and save when full / on demand.
	"""
	def __init__(self, rows=8, cols=4):
		self.rows = rows
		self.cols = cols
		self.fig = None
		self.axs = None
		self.current_ax_index = 0
		self._save_counts = {}

	def _create_fig(self):
		self.fig, self.axs = plt.subplots(self.rows, self.cols, figsize=(self.cols * 3, self.rows * 3))
		self.axs = self.axs.flatten()
		self.current_ax_index = 0

	def get_ase_atoms(self, pmg_structure):
		adaptor = AseAtomsAdaptor()
		return adaptor.get_atoms(pmg_structure)

	def _sanitize(self, s):
		return re.sub(r'[^0-9A-Za-z._-]', '_', str(s))

	def _choose_filename(self, base, key):
		# use internal counter and avoid overwriting existing files
		count = self._save_counts.get(key, 0) + 1
		self._save_counts[key] = count
		if count == 1:
			filename = f"{base}.png"
			if os.path.exists(filename):
				# bump until free
				while os.path.exists(f"{base}_{self._save_counts[key]}.png"):
					self._save_counts[key] += 1
				filename = f"{base}_{self._save_counts[key]}.png"
		else:
			filename = f"{base}_{count}.png"
		return filename

	def plot_slabs_with_side_view_ase(self, ads_structs, material_id, miller_index=None, molecule_type=None, plot_label=None, titles=None):
		# Immediate-save mode when plot_label provided: one PNG per ads_struct (two views)
		if plot_label is not None:
			for ads_struct in ads_structs:
				try:
					ase_atoms = self.get_ase_atoms(ads_struct)
					fig, axs = plt.subplots(1, 2, figsize=(6, 3))
					plot_atoms(ase_atoms, axs[0], rotation='90x')
					# immediate-save: use titles if provided (single item), else Miller
					title0 = titles[0] if titles and len(titles) == 1 and titles[0] else (f"Miller: {miller_index}" if miller_index is not None else "")
					axs[0].set_title(title0)
					plot_atoms(ase_atoms, axs[1], rotation='0x,0y,0z')
					axs[1].set_title(title0)
					plt.tight_layout()

					# If plot_label provided (short basename from .vasp), use it directly as PNG basename (sanitized)
					label_s = self._sanitize(plot_label)
					base = f"{label_s}"
					key = (label_s,)
					filename = self._choose_filename(base, key)

					fig.savefig(filename, dpi=300)
					plt.close(fig)
					print(f"[SlabPlotter] saved immediate PNG: {filename}")
				except Exception as e:
					print(f"[SlabPlotter] immediate-save failed for {plot_label}: {e}")
			return

		# Grouped grid mode
		if self.fig is None:
			self._create_fig()

		for ads_struct in ads_structs:
			# each structure occupies two subplots
			if self.current_ax_index + 2 > len(self.axs):
				# save current figure (use minimal naming) and start a new one
				try:
					self.save_figure(material_id, molecule_type)
				except Exception as e:
					print(f"[SlabPlotter] auto-save failed: {e}")
				self._create_fig()

			try:
				ase_atoms = self.get_ase_atoms(ads_struct)
				# determine per-structure title if titles list provided
				curr_idx = (self.current_ax_index // 2)  # index of structure among those plotted in this figure
				# side view 1
				if self.current_ax_index < len(self.axs):
					ax = self.axs[self.current_ax_index]
					plot_atoms(ase_atoms, ax, rotation='90x')
					# choose title: titles list (per-structure) if provided, else Miller
					tstr = titles[curr_idx] if titles and curr_idx < len(titles) else (f"Miller: {miller_index}" if miller_index is not None else "")
					ax.set_title(tstr)
					self.current_ax_index += 1
				# side view 2
				if self.current_ax_index < len(self.axs):
					ax = self.axs[self.current_ax_index]
					plot_atoms(ase_atoms, ax, rotation='0x,0y,0z')
					ax.set_title(tstr)
					self.current_ax_index += 1
			except Exception as e:
				print(f"[SlabPlotter] plotting failed for grouped mode: {e}")

	def plot_slabs_with_side_view_ase_uudd(self, ads_structs, material_id, miller_index=None, molecule_type=None, plot_label=None):
		# reuse main method behavior
		return self.plot_slabs_with_side_view_ase(ads_structs, material_id, miller_index=miller_index, molecule_type=molecule_type, plot_label=plot_label)

	def save_figure(self, material_id, molecule_type, plot_label=None):
		if not self.fig:
			return
		plt.tight_layout()
		try:
			name = material_id.get('name', str(material_id))
			mpid = material_id.get('mp_id', '')
		except Exception:
			name = str(material_id)
			mpid = ""
		name_s = self._sanitize(name)
		mpid_s = self._sanitize(mpid)
		mol_s = self._sanitize(molecule_type) if molecule_type is not None else "mol"
		label_s = self._sanitize(plot_label) if plot_label else None
		if label_s:
			base = f"slabs-{name_s}-{mpid_s}-{mol_s}-{label_s}"
		else:
			base = f"slabs-{name_s}-{mpid_s}-{mol_s}"

		key = (name_s, mpid_s, mol_s, label_s)
		filename = self._choose_filename(base, key)

		self.fig.savefig(filename, dpi=300)
		plt.close(self.fig)
		self.fig = None
		self.axs = None
		self.current_ax_index = 0
		print(f"[SlabPlotter] saved grouped PNG: {filename}")

	# 新增：为单个 site 绘制不受数量限制的 overview（每个构型占一行，两列：侧/俯视）
	def plot_overview(self, structs, plot_label, molecule_type=None, titles=None):
		"""
		Plot all structs (list of pymatgen Structure) for one site in a single figure.
		Each structure occupies one square-like cell containing two inset axes (side/top).
		"""
		if not structs:
			print(f"[SlabPlotter] no structs to plot for overview {plot_label}")
			return None
		n = len(structs)
		# choose grid to make cells roughly square
		cols = int(np.ceil(np.sqrt(n)))
		rows = int(np.ceil(n / cols))
		fig, axs = plt.subplots(rows, cols, figsize=(cols * 3, rows * 3))
		# normalize axs to 2D array
		if rows == 1 and cols == 1:
			ax_grid = np.array([[axs]])
		elif rows == 1:
			ax_grid = axs.reshape(1, cols)
		elif cols == 1:
			ax_grid = axs.reshape(rows, 1)
		else:
			ax_grid = axs.reshape(rows, cols)

		idx = 0
		for r in range(rows):
			for c in range(cols):
				ax = ax_grid[r, c]
				if idx >= n:
					ax.axis('off')
					continue
				struct = structs[idx]
				# create two inset axes inside this cell: left (side) and right (top)
				try:
					# create inset axes with small left/right margins to avoid overlap
					ax_left = inset_axes(ax, width="46%", height="92%", bbox_to_anchor=(0.03, 0.04, 0.46, 0.92), bbox_transform=ax.transAxes)
					ax_right = inset_axes(ax, width="46%", height="92%", bbox_to_anchor=(0.51, 0.04, 0.46, 0.92), bbox_transform=ax.transAxes)
					ase_atoms = self.get_ase_atoms(struct)
					# draw on inset axes
					plot_atoms(ase_atoms, ax_left, rotation='90x')
					plot_atoms(ase_atoms, ax_right, rotation='0x,0y,0z')
					# remove inset axis frames and ticks for cleaner look
					for ia in (ax_left, ax_right):
						ia.set_xticks([])
						ia.set_yticks([])
						ia.set_frame_on(False)
					# title from provided titles (short_name), shown on the main (frameless) cell
					title = titles[idx] if titles and idx < len(titles) else ""
					ax.set_title(title)
					ax.set_xticks([])
					ax.set_yticks([])
					# hide the main cell frame for a cleaner tile look
					ax.set_frame_on(False)
				except Exception as e:
					print(f"[SlabPlotter] failed plotting overview row {idx} for {plot_label}: {e}")
				idx += 1

		# adjust spacing to avoid overlap between cells
		fig.subplots_adjust(wspace=0.4, hspace=0.6)
		plt.tight_layout()
		# filename uses plot_label
		base = f"{self._sanitize(plot_label)}-overview"
		key = (base,)
		filename = self._choose_filename(base, key)
		fig.savefig(filename, dpi=300)
		plt.close(fig)
		print(f"[SlabPlotter] saved overview PNG: {filename}")
		return filename

	# 新增：把所有 site 的 overview 合并到一张图片中
	def plot_combined_overview(self, site_groups, molecule_type=None, filename_label=None):
		"""
		Plot all sites' structs into a single overview image.
		site_groups: dict site_idx -> list of (structure, short_name)
		"""
		# flatten in site order
		items = []
		for site_idx in sorted(site_groups.keys()):
			entries = site_groups[site_idx]
			for i, (struct, short_name) in enumerate(entries):
				items.append({'struct': struct, 'short_name': short_name, 'site': site_idx, 'first_in_site': (i == 0)})
		if not items:
			print("[SlabPlotter] no items to plot in combined overview")
			return None

		N = len(items)
		cols = int(np.ceil(np.sqrt(N)))
		rows = int(np.ceil(N / cols))
		fig, axs = plt.subplots(rows, cols, figsize=(cols * 3, rows * 3))
		# normalize axs
		if rows == 1 and cols == 1:
			ax_grid = np.array([[axs]])
		elif rows == 1:
			ax_grid = axs.reshape(1, cols)
		elif cols == 1:
			ax_grid = axs.reshape(rows, 1)
		else:
			ax_grid = axs.reshape(rows, cols)

		idx = 0
		for r in range(rows):
			for c in range(cols):
				ax = ax_grid[r, c]
				if idx >= N:
					ax.axis('off')
					continue
				item = items[idx]
				struct = item['struct']
				short_name = item['short_name']
				site_idx = item['site']
				first = item['first_in_site']
				try:
					# inset left/right
					ax_left = inset_axes(ax, width="46%", height="92%", bbox_to_anchor=(0.03, 0.04, 0.46, 0.92), bbox_transform=ax.transAxes)
					ax_right = inset_axes(ax, width="46%", height="92%", bbox_to_anchor=(0.51, 0.04, 0.46, 0.92), bbox_transform=ax.transAxes)
					ase_atoms = self.get_ase_atoms(struct)
					plot_atoms(ase_atoms, ax_left, rotation='90x')
					plot_atoms(ase_atoms, ax_right, rotation='0x,0y,0z')
					for ia in (ax_left, ax_right):
						ia.set_xticks([])
						ia.set_yticks([])
						ia.set_frame_on(False)
					# main cell title: include site label for first item of each site
					title = f"site{site_idx}: {short_name}" if first else short_name
					ax.set_title(title)
					ax.set_xticks([])
					ax.set_yticks([])
					ax.set_frame_on(False)
				except Exception as e:
					print(f"[SlabPlotter] failed plotting combined cell {idx}: {e}")
				idx += 1

		fig.subplots_adjust(wspace=0.35, hspace=0.5)
		plt.tight_layout()
		# filename
		if filename_label:
			base = self._sanitize(filename_label)
		else:
			if molecule_type:
				base = f"{self._sanitize(molecule_type)}-all-sites-overview"
			else:
				base = "all-sites-overview"
		key = (base,)
		filename = self._choose_filename(base, key)
		fig.savefig(filename, dpi=300)
		plt.close(fig)
		print(f"[SlabPlotter] saved combined overview PNG: {filename}")
		return filename

class BulkPlotter:
	def __init__(self, rows=7, cols=4):
		self.fig, self.axs = plt.subplots(rows, cols, figsize=(cols * 3, rows * 3))
		self.current_ax_index = 0
		if rows * cols == 1:
			self.axs = [self.axs]
		else:
			self.axs = self.axs.flatten()

	def plot_bulk(self, bulk_struct, title="Bulk"):
		if self.current_ax_index < len(self.axs):
			ase_atoms = AseAtomsAdaptor().get_atoms(bulk_struct)
			ax = self.axs[self.current_ax_index]
			plot_atoms(ase_atoms, ax, rotation='30x,-30y,30z')
			formula = bulk_struct.composition.reduced_formula
			ax.set_title(f"{title}: {formula}")
			self.current_ax_index += 1
		else:
			print("Reached the maximum number of plots. Increase rows/cols or reset the index.")

	def save_figure(self, filename="bulk_structures.png"):
		self.fig.savefig(filename)
		plt.close(self.fig)
