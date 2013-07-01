# Copyright 2012 mdtraj developers
#
# This file is part of mdtraj
#
# mdtraj is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# mdtraj is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# mdtraj. If not, see http://www.gnu.org/licenses/.

import tempfile, os
from mdtraj.testing import get_fn, eq, DocStringFormatTester, assert_raises
import numpy as np
from mdtraj.trajectory import load
import mdtraj.trajectory
from mdtraj import topology

TestDocstrings = DocStringFormatTester(mdtraj.trajectory, error_on_none=True)

fn = get_fn('traj.h5')
nat = get_fn('native.pdb')
temp1 = tempfile.mkstemp(suffix='.xtc')[1]
temp2 = tempfile.mkstemp(suffix='.dcd')[1]
temp3 = tempfile.mkstemp(suffix='.binpos')[1]
temp4 = tempfile.mkstemp(suffix='.trr')[1]
temp5 = tempfile.mkstemp(suffix='.h5')[1]
temp6 = tempfile.mkstemp(suffix='.pdb')[1]
temp7 = tempfile.mkstemp(suffix='.nc')[1]

def teardown_module(module):
    """remove the temporary file created by tests in this file
    this gets automatically called by nose"""
    for e in [temp1, temp2, temp3, temp4, temp5, temp6, temp7]:
        os.unlink(e)


def test_legacy_hdf0():
    t0 = load(fn)


def test_mismatch():
    # loading a 22 atoms xtc with a topology that has 2,000 atoms
    # some kind of error should happen!
    with assert_raises(ValueError):
        load(get_fn('frame0.xtc'), top=get_fn('4K6Q.pdb'))


def test_box():
    t = load(get_fn('native.pdb'))
    yield lambda: eq(t.unitcell_vectors, None)
    yield lambda: eq(t.unitcell_lengths, None)
    yield lambda: eq(t.unitcell_angles, None)

    t.unitcell_vectors = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]]).reshape(1, 3, 3)
    yield lambda: eq(np.array([1.0, 1.0, 1.0]), t.unitcell_lengths[0])
    yield lambda: eq(np.array([90.0, 90.0, 90.0]), t.unitcell_angles[0])


def test_load_pdb_box():
    t = load(get_fn('native2.pdb'))
    yield lambda: eq(t.unitcell_lengths[0], np.array([0.1, 0.2, 0.3]))
    yield lambda: eq(t.unitcell_angles[0], np.array([90.0, 90.0, 90.0]))
    yield lambda: eq(t.unitcell_vectors[0], np.array([[0.1, 0, 0], [0, 0.2, 0], [0, 0, 0.3]]))


def test_box_load_save():
    t = load(get_fn('native2.pdb'))

    # these three tempfile have extensions (dcd, xtc, trr) that
    # should store the box information. lets make sure than through a load/save
    # cycle, the box information is preserved:
    for temp_fn in [temp1, temp2, temp4, temp5]:
        t.save(temp_fn)
        if temp_fn.endswith('.h5'):
            t2 = load(temp_fn)
        else:
            t2 = load(temp_fn, top=get_fn('native.pdb'))

        assert t.unitcell_vectors != None
        yield lambda: eq(t.xyz, t2.xyz, decimal=3)
        yield lambda: eq(t.unitcell_vectors, t2.unitcell_vectors)
        yield lambda: eq(t.unitcell_angles, t2.unitcell_angles)
        yield lambda: eq(t.unitcell_lengths, t2.unitcell_lengths)


def test_legacy_hdf_frame():
    t0 = load(fn)
    t1 = load(fn, frame=1)

    yield lambda: eq(t0[1].xyz, t1.xyz)
    yield lambda: eq(t0[1].unitcell_vectors, t1.unitcell_vectors)
    yield lambda: eq(t0[1].unitcell_angles, t1.unitcell_angles)
    yield lambda: eq(t0[1].unitcell_lengths, t1.unitcell_lengths)
    yield lambda: eq(t0[1].time, t1.time)


def test_slice():
    t = load(fn)
    yield lambda: eq((t[0:5] + t[5:10]).xyz, t[0:10].xyz)
    yield lambda: eq((t[0:5] + t[5:10]).time, t[0:10].time)
    yield lambda: eq((t[0:5] + t[5:10]).unitcell_vectors, t[0:10].unitcell_vectors)
    yield lambda: eq((t[0:5] + t[5:10]).unitcell_lengths, t[0:10].unitcell_lengths)
    yield lambda: eq((t[0:5] + t[5:10]).unitcell_angles, t[0:10].unitcell_angles)


def test_slice2():
    t = load(get_fn('traj.h5'))
    yield lambda: t[0] == t[[0,1]][0]


def test_xtc():
    t = mdtraj.trajectory.load(get_fn('frame0.xtc'), top=nat)
    for e in [temp1, temp2, temp3, temp4]:
        def f():
            t.save(e)
            t2 = mdtraj.trajectory.load(e, top=nat)
            eq(t.xyz, t2.xyz, err_msg=e)

            # ony trr and xtc save the time that we read from the original
            # xtc format
            if e.endswith('.trr') or e.endswith('.xtc'):
                eq(t.time, t2.time, err_msg=e)
        yield f


def test_dcd():
    t = mdtraj.trajectory.load(get_fn('frame0.dcd'), top=nat)
    for e in [temp1, temp2, temp3, temp4]:
        def f():
            t.save(e)
            t2 = mdtraj.trajectory.load(e, top=nat)
            eq(t.xyz, t2.xyz, err_msg=e)
            eq(t.time, t2.time, err_msg=e)
        yield f


def test_binpos():
    t = mdtraj.trajectory.load(get_fn('frame0.binpos'), top=nat)
    for e in [temp1, temp2, temp3, temp4]:
        def f():
            t.save(e)
            t2 = mdtraj.trajectory.load(e, top=nat)
            eq(t.xyz, t2.xyz, err_msg=e)
            eq(t.time, t2.time, err_msg=e)
        yield f


def test_load_join():
    filenames = ["frame0.xtc", "frame0.trr", "frame0.dcd", "frame0.binpos"] #, "traj.h5"]
    num_block = 3
    for filename in filenames:
        t0 = mdtraj.trajectory.load(get_fn(filename), top=nat, discard_overlapping_frames=True)
        t1 = mdtraj.trajectory.load(get_fn(filename), top=nat, discard_overlapping_frames=False)
        t2 = mdtraj.trajectory.load([get_fn(filename) for i in xrange(num_block)], top=nat, discard_overlapping_frames=False)
        t3 = mdtraj.trajectory.load([get_fn(filename) for i in xrange(num_block)], top=nat, discard_overlapping_frames=True)

        yield lambda: eq(t0.n_frames, t1.n_frames)
        yield lambda: eq(t0.n_frames * num_block, t2.n_frames)
        yield lambda: eq(t3.n_frames , t0.n_frames * num_block - num_block + 1)

    # h5 loader doesn't need top
    t0 = mdtraj.trajectory.load(get_fn('traj.h5'), discard_overlapping_frames=True)
    t1 = mdtraj.trajectory.load(get_fn('traj.h5'), discard_overlapping_frames=False)
    t2 = mdtraj.trajectory.load([get_fn('traj.h5') for i in xrange(num_block)], discard_overlapping_frames=False)
    t3 = mdtraj.trajectory.load([get_fn('traj.h5') for i in xrange(num_block)], discard_overlapping_frames=True)
    yield lambda: eq(t0.n_frames, t1.n_frames)
    yield lambda: eq(t0.n_frames * num_block, t2.n_frames)
    yield lambda: eq(t3.n_frames , t0.n_frames * num_block - num_block + 1)


def test_hdf5_0():
    t = load(get_fn('traj.h5'))
    t2 = load(get_fn('native.pdb'))
    t3 = load(get_fn('traj.h5'), frame=8)

    assert t.topology == t2.topology
    yield lambda: eq(t.time, 0.002*(1 + np.arange(100)))
    yield lambda: eq(t.time, 0.002*(1 + np.arange(100)))
    yield lambda: eq(t[8].xyz, t3.xyz)
    yield lambda: eq(t[8].time, t3.time)
    yield lambda: eq(t[8].unitcell_vectors, t3.unitcell_vectors)


def test_center():
    traj = load(get_fn('traj.h5'))
    traj.center_coordinates()
    mu = traj.xyz.mean(1)
    mu0 = np.zeros(mu.shape)
    eq(mu0, mu)


def test_restrict_atoms():
    traj = load(get_fn('traj.h5'))
    desired_atom_indices = [0,1,2,5]
    traj.restrict_atoms(desired_atom_indices)
    atom_indices = [a.index for a in traj.top.atoms]
    eq([0,1,2,3], atom_indices)
    eq(traj.xyz.shape[1], 4)
    eq(traj.n_atoms, 4)
    eq(traj.n_residues, 1)
    eq(len(traj.top._bonds), 2)
    eq(traj.n_residues, traj.topology._numResidues)
    eq(traj.n_atoms, traj.topology._numAtoms)
    eq(np.array([a.index for a in traj.topology.atoms]), np.arange(traj.n_atoms))


def test_array_vs_matrix():
    top = load(get_fn('native.pdb')).topology
    xyz = np.random.randn(1, 22, 3)
    xyz_mat = np.matrix(xyz)
    t1 = mdtraj.trajectory.Trajectory(xyz, top)
    t2 = mdtraj.trajectory.Trajectory(xyz_mat, top)

    eq(t1.xyz, xyz)
    eq(t2.xyz, xyz)

def test_pdb_unitcell_loadsave():
    """Make sure that nonstandard unitcell dimensions are saved and loaded
    correctly with PDB"""
    tref = load(get_fn('native.pdb'))
    tref.unitcell_lengths = 1 + 0.1  * np.random.randn(tref.n_frames, 3)
    tref.unitcell_angles = 90 + 0.0  * np.random.randn(tref.n_frames, 3)
    tref.save(temp6)

    tnew = load(temp6)
    eq(tref.unitcell_vectors, tnew.unitcell_vectors, decimal=3)


def test_load_combination():
    "Test that the load() function's stride and atom_indices work accross all trajectory formats"

    topology = load(get_fn('native.pdb')).topology
    ainds = np.array([a.index for a in topology.atoms if a.element.symbol == 'C'])
    filenames = ['frame0.binpos', 'frame0.dcd', 'frame0.trr', 'frame0.xtc', 'frame0.nc', 'frame0.h5', 'frame0.pdb']

    no_kwargs = [load(fn, top=topology) for fn in map(get_fn, filenames)]
    strided3 =  [load(fn, top=topology, stride=3) for fn in map(get_fn, filenames)]
    subset =    [load(fn, top=topology, atom_indices=ainds) for fn in map(get_fn, filenames)]


    for i, (t1, t2) in enumerate(zip(no_kwargs, strided3)):
        yield lambda: eq(t1.xyz[::3], t2.xyz)
        yield lambda: eq(t1.time[::3], t2.time)
        if t1.unitcell_vectors != None:
            yield lambda: eq(t1.unitcell_vectors[::3], t2.unitcell_vectors)
        yield lambda: eq(t1.topology, t2.topology)

    for i, (t1, t2) in enumerate(zip(no_kwargs, subset)):
        yield lambda: eq(t1.xyz[:, ainds, :], t2.xyz)
        yield lambda: eq(t1.time, t2.time)
        if t1.unitcell_vectors != None:
            yield lambda: eq(t1.unitcell_vectors, t2.unitcell_vectors)
        yield lambda: eq(t1.topology.subset(ainds), t2.topology)