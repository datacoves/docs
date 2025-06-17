defmodule Jade.Files.FileRepoTest do
  use Jade.DataCase, async: true

  alias Jade.Files.File
  alias Jade.Files.FileRepo

  @invalid_attrs %{tag: nil, filename: nil, path: nil}
  describe "get_file_by/1" do
    test "returns the file with the given attributes" do
      file = insert(:file)

      # Ensure the file is not returned with its content
      file = %{file | contents: nil}
      assert {:ok, ^file} = FileRepo.get_file_by(tag: file.tag)
      assert {:ok, ^file} = FileRepo.get_file_by(filename: file.filename)
      assert {:ok, ^file} = FileRepo.get_file_by(path: file.path)
    end

    test "returns not found error if no file matches the attributes" do
      assert {:error, :not_found} == FileRepo.get_file_by(tag: "nonexistent")
    end
  end

  describe "get_files_by/1" do
    test "returns the files with the given attributes" do
      file1 = insert(:file, %{tag: "tag1", filename: "file1.txt", path: "path1"})
      file2 = insert(:file, %{tag: "tag1", filename: "file1.txt", path: "path1"})
      _ignore_file = insert(:file, %{tag: "tag2", filename: "file2.txt", path: "path2"})

      # Ensure the file is not returned with its content
      file1 = %{file1 | contents: nil}
      file2 = %{file2 | contents: nil}
      assert {:ok, [^file1, ^file2]} = FileRepo.get_files_by(tag: "tag1")
      assert {:ok, [^file1, ^file2]} = FileRepo.get_files_by(filename: "file1.txt")
      assert {:ok, [^file1, ^file2]} = FileRepo.get_files_by(path: "path1")
    end

    test "returns not fount error if no files match the attributes" do
      assert {:error, :not_found} == FileRepo.get_files_by(tag: "nonexistent")
    end
  end

  test "create_file/1 with valid data creates a file" do
    valid_attrs = %{
      tag: "some tag",
      filename: "some filename.pdf",
      path: "some path",
      contents: "testtesttest",
      environment_slug: "test_environment"
    }

    assert {:ok, %File{} = file} = FileRepo.create_file(valid_attrs)
    assert file.tag == "some tag"
    assert file.filename == "some filename.pdf"
    assert file.environment_slug == "test_environment"
    assert file.path == "/environments/test_environment/files/some-tag/some-filename.pdf"
  end

  test "create_file/1 with invalid data returns error changeset" do
    assert {:error, %Ecto.Changeset{}} = FileRepo.create_file(@invalid_attrs)
  end

  test "update_file/2 with valid data updates the file" do
    file = insert(:file)

    update_attrs = %{
      tag: "some updated tag",
      filename: "some updated filename.json",
      environment_slug: "env234",
      contents: "test123test"
    }

    assert {:ok, %File{} = updated_file} = FileRepo.update_file(file, update_attrs)
    assert updated_file.tag == "some updated tag"
    assert updated_file.filename == "some updated filename.json"
    assert updated_file.contents == "test123test"
    assert updated_file.environment_slug == "env234"

    assert updated_file.path ==
             "/environments/env234/files/some-updated-tag/some-updated-filename.json"
  end

  test "update_file/2 with invalid data returns error changeset" do
    file = insert(:file)
    assert {:error, %Ecto.Changeset{}} = FileRepo.update_file(file, @invalid_attrs)
  end

  test "delete_file/1 deletes the file" do
    file = insert(:file)
    assert {:ok, %File{}} = FileRepo.delete_file(file)
    assert_raise Ecto.NoResultsError, fn -> FileRepo.get_file!(file.slug) end
  end
end
